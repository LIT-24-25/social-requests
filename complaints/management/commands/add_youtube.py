from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Optional, Tuple
from complaints.models import Complaint
from gigachat import GigaChat
from clusters.instances import youtube_api_key, gigachat_token
from tqdm import tqdm
import random
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import comments from a YouTube video and add them to the database'

    def add_arguments(self, parser):
        parser.add_argument('video_url', type=str, help='URL of the YouTube video')
        parser.add_argument(
            '--max-results',
            type=int,
            default=1000,
            help='Maximum number of comments to retrieve (default: 1000)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of comments to process in one batch (default: 50)'
        )

    def get_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            str: Video ID if found, None otherwise
            
        Raises:
            ValueError: If the URL is invalid or not a YouTube URL
        """
        if not url:
            raise ValueError("YouTube URL cannot be empty")
            
        parsed_url = urlparse(url)
        
        # Validate basic URL structure
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
            
        # Check if it's a YouTube domain
        if not ('youtube.com' in parsed_url.hostname or 'youtu.be' in parsed_url.hostname):
            raise ValueError("URL is not from YouTube")
        
        # Extract video ID based on different URL formats
        if 'youtube.com' in parsed_url.hostname:
            # Standard watch URLs: youtube.com/watch?v=VIDEO_ID
            if '/watch' in parsed_url.path:
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
                    
            # Short URLs: youtube.com/shorts/VIDEO_ID
            elif '/shorts/' in parsed_url.path:
                path_parts = parsed_url.path.split('/')
                if len(path_parts) > 2:
                    return path_parts[2]
                    
            # Embedded URLs: youtube.com/embed/VIDEO_ID
            elif '/embed/' in parsed_url.path:
                path_parts = parsed_url.path.split('/')
                if len(path_parts) > 2:
                    return path_parts[2]
                    
            # Video direct URLs: youtube.com/v/VIDEO_ID
            elif parsed_url.path.startswith('/v/'):
                path_parts = parsed_url.path.split('/')
                if len(path_parts) > 2:
                    return path_parts[2]
        
        # Short-form youtu.be URLs: youtu.be/VIDEO_ID
        elif 'youtu.be' in parsed_url.hostname:
            if parsed_url.path and parsed_url.path != '/':
                # Remove leading slash
                return parsed_url.path[1:].split('/')[0]
        
        # If we get here, we couldn't extract a video ID
        raise ValueError("Could not extract video ID from URL. Please use a standard YouTube URL format.")

    def get_comment_replies(self, youtube, parent_id: str, max_results: int = 100) -> List[Dict]:
        """
        Retrieve replies for a specific comment.
        
        Args:
            youtube: YouTube API client
            parent_id (str): ID of the parent comment
            max_results (int): Maximum number of replies to retrieve
            
        Returns:
            List[Dict]: List of reply comments
        """
        replies = []
        try:
            request = youtube.comments().list(
                part="snippet",
                parentId=parent_id,
                maxResults=max_results,
                textFormat="plainText"
            )

            while request and len(replies) < max_results:
                response = request.execute()
                
                for item in response['items']:
                    replies.append({
                        'name': item['snippet']['authorDisplayName'],
                        'email': item['snippet']['authorChannelUrl'],
                        'text': item['snippet']['textDisplay'],
                    })

                if 'nextPageToken' in response and len(replies) < max_results:
                    request = youtube.comments().list(
                        part="snippet",
                        parentId=parent_id,
                        pageToken=response['nextPageToken'],
                        maxResults=min(max_results - len(replies), 100),
                        textFormat="plainText"
                    )
                else:
                    request = None

            return replies
        except Exception as e:
            logger.warning(f"Error fetching replies for comment {parent_id}: {str(e)}")
            return []

    def get_youtube_comments(self, video_url: str, max_results: int = 100) -> List[Dict]:
        """
        Retrieve comments and their replies from a YouTube video.
        
        Args:
            video_url (str): URL of the YouTube video
            max_results (int): Maximum number of top-level comments to retrieve
            
        Returns:
            List[Dict]: List of comments and their replies
            
        Raises:
            ValueError: If the video URL is invalid
            ConnectionError: If there's an error connecting to the YouTube API
            Exception: If there's an error accessing the YouTube API
        """
        try:
            video_id = self.get_video_id(video_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL - could not extract video ID")

            # Try to build the YouTube service
            try:
                youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to YouTube API: {str(e)}")

            all_comments = []
            top_level_count = 0

            try:
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(max_results, 100),
                    textFormat="plainText"
                )

                while request and top_level_count < max_results:
                    try:
                        response = request.execute()
                    except Exception as e:
                        raise ConnectionError(f"Failed to fetch comments from YouTube API: {str(e)}")
                    
                    if 'items' not in response or not response['items']:
                        self.stdout.write("No comments found for this video or comments may be disabled.")
                        break
                    
                    for item in response['items']:
                        comment = item['snippet']['topLevelComment']['snippet']
                        comment_id = item['snippet']['topLevelComment']['id']
                        
                        # Add top-level comment
                        all_comments.append({
                            'name': comment['authorDisplayName'],
                            'email': comment['authorChannelUrl'],
                            'text': comment['textDisplay'],
                        })
                        top_level_count += 1

                        # Check if comment has replies
                        if item.get('snippet', {}).get('totalReplyCount', 0) > 0:
                            # Fetch all replies for this comment
                            replies = self.get_comment_replies(youtube, comment_id)
                            all_comments.extend(replies)

                    if 'nextPageToken' in response and top_level_count < max_results:
                        request = youtube.commentThreads().list(
                            part="snippet,replies",
                            videoId=video_id,
                            pageToken=response['nextPageToken'],
                            maxResults=min(max_results - top_level_count, 100),
                            textFormat="plainText"
                        )
                    else:
                        request = None
                
                self.stdout.write(f"Found {len(all_comments)} total comments ({top_level_count} top-level comments and {len(all_comments) - top_level_count} replies)")
                
                if not all_comments:
                    self.stdout.write(self.style.WARNING("No comments were retrieved. The video might have comments disabled."))
                
                return all_comments

            except Exception as e:
                if "commentsDisabled" in str(e):
                    raise ValueError("Comments are disabled for this video")
                elif "videoNotFound" in str(e):
                    raise ValueError("Video not found - it might be private or deleted")
                else:
                    raise Exception(f"Error fetching comments: {str(e)}")

        except ValueError as e:
            # Re-raise validation errors
            raise
        except ConnectionError as e:
            # Re-raise connection errors
            raise
        except Exception as e:
            # Convert other errors to a generic exception
            raise Exception(f"Error processing YouTube URL: {str(e)}")

    def prepare_batches(self, comments: List[Dict], batch_size: int) -> Tuple[List[Complaint], List[str]]:
        """
        Prepare batches of complaints and their text for batch embedding processing.
        
        Args:
            comments (List[Dict]): List of comment dictionaries
            batch_size (int): Size of each batch
            
        Returns:
            Tuple[List[Complaint], List[str]]: Tuple containing list of complaint objects and 
                                              list of their texts for batch processing
        """
        complaints = []
        texts = []
        
        for comment in tqdm(comments, desc="Preparing complaints", unit="comment"):
            try:
                complaint = Complaint(
                    name=comment['name'],
                    email=comment['email'],
                    text=comment['text'],
                    x=random.randint(0, 100),
                    y=random.randint(0, 100)
                )
                complaints.append(complaint)
                texts.append(comment['text'])
            except Exception as e:
                logger.error(f"Error creating complaint for {comment['name']}: {str(e)}")
                continue
        
        return complaints, texts

    def process_batches(self, complaints, texts, batch_size):
        """
        Process complaints in batches for more efficient embedding generation.
        
        Args:
            complaints (List[Complaint]): List of complaint objects
            texts (List[str]): List of complaint texts for embedding
            batch_size (int): Size of each batch
            
        Returns:
            List[Complaint]: List of processed complaints with embeddings
        """
        processed_complaints = []
        
        # Process in batches
        batches = [
            (complaints[i:i + batch_size], texts[i:i + batch_size])
            for i in range(0, len(complaints), batch_size)
        ]
        
        logger.info(f"Processing {len(complaints)} complaints in {len(batches)} batches of {batch_size}")
        
        # Initialize GigaChat client once
        giga_client = GigaChat(credentials=gigachat_token, verify_ssl_certs=False)
        
        # Create progress bar for batch processing
        batch_pbar = tqdm(batches, desc="Processing batches", unit="batch")
        
        for batch_index, (complaint_batch, text_batch) in enumerate(batch_pbar, 1):
            batch_pbar.set_description(f"Processing batch {batch_index}/{len(batches)}")
            
            try:
                # Use the static method for batch processing
                processed_batch = Complaint.batch_process_embeddings(
                    complaint_batch, text_batch, giga_client
                )
                processed_complaints.extend(processed_batch)
                logger.info(f"Successfully processed batch {batch_index}/{len(batches)}")
            except Exception as e:
                logger.error(f"Error processing batch {batch_index}: {str(e)}")
                # Continue with next batch even if this one fails
                continue
            
        return processed_complaints

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        video_url = options['video_url']
        max_results = options['max_results']
        batch_size = options['batch_size']

        logger.info("Starting YouTube comments processing")
        
        # Create a progress bar for tracking overall progress
        overall_progress = tqdm(total=4, desc="Overall process", position=0)
        
        try:
            # Fetch comments from YouTube
            overall_progress.set_description("Fetching YouTube comments")
            try:
                comments = self.get_youtube_comments(video_url, max_results)
                logger.info(f"Successfully retrieved {len(comments)} total comments")
            except ValueError as e:
                # URL validation errors
                overall_progress.close()
                logger.error(f"YouTube URL validation error: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Invalid YouTube URL: {str(e)}"))
                return
            except ConnectionError as e:
                # Connection errors
                overall_progress.close()
                logger.error(f"YouTube API connection error: {str(e)}")
                self.stdout.write(self.style.ERROR(f"Connection error: {str(e)}"))
                return
            except Exception as e:
                # Other API errors
                overall_progress.close()
                logger.error(f"YouTube API error: {str(e)}")
                self.stdout.write(self.style.ERROR(f"YouTube API error: {str(e)}"))
                return
            
            overall_progress.update(1)
            
            # If no comments were found but no error was raised
            if not comments:
                overall_progress.close()
                logger.warning("No comments found for the video. The video might have comments disabled.")
                self.stdout.write(self.style.WARNING("No comments found for the video. The video might have comments disabled."))
                return
            
            # Prepare batches of complaints and their texts
            overall_progress.set_description("Preparing complaint batches")
            complaints, texts = self.prepare_batches(comments, batch_size)
            logger.info(f"Prepared {len(complaints)} complaints for batch processing")
            overall_progress.update(1)
            
            # Process batches
            overall_progress.set_description("Processing complaint batches")
            processed_complaints = self.process_batches(complaints, texts, batch_size)
            logger.info(f"Successfully processed {len(processed_complaints)} complaints with embeddings")
            overall_progress.update(1)
            
            # Save processed complaints to database
            overall_progress.set_description("Saving to database")
            if processed_complaints:
                created_complaints = Complaint.objects.bulk_create(processed_complaints, batch_size=100)
                success_count = len(created_complaints)
                logger.info(f"Saved {success_count} complaints to database")
            else:
                success_count = 0
                logger.warning("No complaints were processed successfully")
            overall_progress.update(1)
            
            # Close the progress bar
            overall_progress.close()
            
            logger.info("Completed processing all YouTube comments")
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {success_count} out of {len(complaints)} comments'
                )
            )
        except Exception as e:
            # Make sure to close the progress bar on error
            overall_progress.close()
            logger.error(f"Failed to process YouTube comments: {str(e)}")
            raise CommandError(str(e)) 