from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs
from clusters.instances import youtube_api_key
import os
from typing import List, Dict, Optional

def get_video_id(url: str) -> Optional[str]:
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

def get_youtube_comments(video_url: str, api_key: str, max_results: int = 100) -> List[Dict]:
    """
    Retrieve comments from a YouTube video.
    
    Args:
        video_url (str): URL of the YouTube video
        api_key (str): YouTube Data API key
        max_results (int): Maximum number of comments to retrieve (default: 100)
        
    Returns:
        List[Dict]: List of comments, each containing 'author', 'text', and 'publishedAt'
        
    Raises:
        ValueError: If the video URL is invalid
        Exception: If there's an error accessing the YouTube API
    """
    video_id = get_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    youtube = build('youtube', 'v3', developerKey=youtube_api_key)
    comments = []

    try:
        # Get comments from the video
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            textFormat="plainText"
        )

        while request and len(comments) < max_results:
            response = request.execute()
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'id': item['snippet']['topLevelComment']['id'],  # Comment ID
                    'name': comment['authorDisplayName'],
                    'text': comment['textDisplay'],
                    'channel_url': comment['authorChannelUrl']  # Commentator's channel URL
                })

            # Check if there are more comments
            if 'nextPageToken' in response and len(comments) < max_results:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=min(max_results - len(comments), 100),
                    textFormat="plainText"
                )
            else:
                request = None

        for comment in comments:
            print(f"ID: {comment['id']}")
            print(f"Channel URL: {comment['channel_url']}")
            print(f"Name: {comment['name']}")
            print(f"Comment: {comment['text']}")
            print("-" * 50)
        return comments

    except Exception as e:
        raise Exception(f"Error fetching comments: {str(e)}")