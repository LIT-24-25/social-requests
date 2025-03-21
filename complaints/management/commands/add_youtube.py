from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Optional
from complaints.models import Complaint
from gigachat import GigaChat
from clusters.instances import youtube_api_key, gigachat_token
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
            default=100,
            help='Maximum number of comments to retrieve (default: 100)'
        )

    def get_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            str: Video ID if found, None otherwise
        """
        parsed_url = urlparse(url)
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        return None

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
            Exception: If there's an error accessing the YouTube API
        """
        video_id = self.get_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        youtube = build('youtube', 'v3', developerKey=youtube_api_key)
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
                response = request.execute()
                
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
            return all_comments

        except Exception as e:
            raise Exception(f"Error fetching comments: {str(e)}")

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        video_url = options['video_url']
        max_results = options['max_results']

        logger.info("Starting YouTube comments processing")
        try:
            comments = self.get_youtube_comments(video_url, max_results)
            logger.info(f"Successfully retrieved {len(comments)} total comments")
            
            giga_client = GigaChat(credentials=gigachat_token, verify_ssl_certs=False)
            logger.info("Connected to GigaChat service")
            
            success_count = 0
            for i, comment in enumerate(comments, 1):
                try:
                    complaint = Complaint(
                        name=comment['name'],
                        email=comment['email'],
                        text=comment['text'],
                        x=random.randint(0, 100),
                        y=random.randint(0, 100)
                    )
                    complaint.call_gigachat_embeddings(complaint.text, giga_client)
                    complaint.save()
                    success_count += 1
                    logger.debug(f"Processed comment {i}/{len(comments)} from user {comment['name']}")
                except Exception as e:
                    logger.error(f"Error processing comment {i} from {comment['name']}: {str(e)}")
                    continue
            
            logger.info("Completed processing all YouTube comments")
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {success_count} out of {len(comments)} comments'
                )
            )
        except Exception as e:
            logger.error(f"Failed to process YouTube comments: {str(e)}")
            raise CommandError(str(e)) 