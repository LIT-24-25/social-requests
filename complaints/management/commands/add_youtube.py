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
        parser.add_argument('project_id', type=int, help='ID of the project')

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

    def get_comment_replies(self, youtube, parent_id: str) -> List[Dict]:
        """
        Retrieve replies for a specific comment.
        
        Args:
            youtube: YouTube API client
            parent_id (str): ID of the parent comment
            
        Returns:
            List[Dict]: List of reply comments
        """
        replies = []
        try:
            request = youtube.comments().list(
                part="snippet",
                parentId=parent_id,
                textFormat="plainText"
            )

            while request:
                response = request.execute()
                
                for item in response['items']:
                    replies.append({
                        'name': item['snippet']['authorDisplayName'],
                        'email': item['snippet']['authorChannelUrl'],
                        'text': item['snippet']['textDisplay'],
                    })

                if 'nextPageToken' in response:
                    request = youtube.comments().list(
                        part="snippet",
                        parentId=parent_id,
                        pageToken=response['nextPageToken'],
                        textFormat="plainText"
                    )
                else:
                    request = None

            return replies
        except Exception as e:
            logger.warning(f"Error fetching replies for comment {parent_id}: {str(e)}")
            return []

    def get_youtube_comments(self, video_url: str) -> List[Dict]:
        """
        Retrieve comments and their replies from a YouTube video.
        
        Args:
            video_url (str): URL of the YouTube video
            
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

            try:
                youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to YouTube API: {str(e)}")

            all_comments = []
            logger.info("Starting to fetch comments from YouTube API")

            try:
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    textFormat="plainText"
                )

                pbar = None
                while request:
                    try:
                        response = request.execute()
                    except Exception as e:
                        raise ConnectionError(f"Failed to fetch comments from YouTube API: {str(e)}")
                    
                    if 'items' not in response or not response['items']:
                        raise ValueError("No comments found for this video or comments may be disabled.")
                    
                    if pbar is None:
                        total_results = response.get('pageInfo', {}).get('totalResults', 0)
                        pbar = tqdm(total=total_results, desc="Fetching comments", unit="comment")
                    
                    for item in response['items']:
                        comment = item['snippet']['topLevelComment']['snippet']
                        comment_id = item['snippet']['topLevelComment']['id']
                        
                        all_comments.append({
                            'name': comment['authorDisplayName'],
                            'email': comment['authorChannelUrl'],
                            'text': comment['textDisplay'],
                        })

                        if item.get('snippet', {}).get('totalReplyCount', 0) > 0:
                            logger.debug(f"Fetching replies for comment {comment_id}")
                            replies = self.get_comment_replies(youtube, comment_id)
                            all_comments.extend(replies)
                        
                        pbar.update(1)

                    if 'nextPageToken' in response:
                        request = youtube.commentThreads().list(
                            part="snippet,replies",
                            videoId=video_id,
                            pageToken=response['nextPageToken'],
                            textFormat="plainText"
                        )
                    else:
                        request = None
                
                if pbar:
                    pbar.close()
                
                if not all_comments:
                    raise ValueError("No comments were retrieved. The video might have comments disabled.")
                
                logger.info(f"Successfully retrieved {len(all_comments)} comments and replies")
                return all_comments

            except Exception as e:
                if "commentsDisabled" in str(e):
                    raise ValueError("Comments are disabled for this video")
                elif "videoNotFound" in str(e):
                    raise ValueError("Video not found - it might be private or deleted")
                else:
                    raise Exception(f"Error fetching comments: {str(e)}")

        except ValueError as e:
            raise
        except ConnectionError as e:
            raise
        except Exception as e:
            raise Exception(f"Error processing YouTube URL: {str(e)}")

    def prepare_batches(self, comments: List[Dict], batch_size: int, project_id: int) -> Tuple[List[Complaint], List[str]]:
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
                    y=random.randint(0, 100),
                    project_id=project_id
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

    def calculate_batch_size(self, total_comments: int) -> int:
        """
        Calculate optimal batch size based on number of comments.
        
        Args:
            total_comments (int): Total number of comments
            
        Returns:
            int: Calculated batch size
        """
        if total_comments <= 50:
            return 10
        elif total_comments <= 200:
            return 25
        elif total_comments <= 500:
            return 50
        else:
            return 100

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        video_url = options['video_url']
        project_id = options['project_id']
        
        logger.info("Starting YouTube comments processing")
        
        try:
            comments = self.get_youtube_comments(video_url)
            if not comments:
                raise ValueError("No comments found for the video")

            batch_size = self.calculate_batch_size(len(comments))
            logger.info(f"Using batch size of {batch_size} for {len(comments)} comments")
                
            complaints, texts = self.prepare_batches(comments, batch_size, project_id)
            if not complaints:
                raise ValueError("Failed to prepare complaints from comments")
                
            processed_complaints = self.process_batches(complaints, texts, batch_size)
            if not processed_complaints:
                raise ValueError("Failed to process complaints")
                
            created_complaints = Complaint.objects.bulk_create(processed_complaints, batch_size=100)
            if not created_complaints:
                raise ValueError("Failed to save complaints to database")
                
            logger.info("Completed processing all YouTube comments")
            self.stdout.write(
                self.style.SUCCESS(
                    f'YouTube comments successfully imported! ({len(created_complaints)} comments)'
                )
            )
        except Exception as e:
            logger.error(f"Failed to process YouTube comments: {str(e)}")
            raise CommandError(str(e)) 