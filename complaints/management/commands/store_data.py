import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_requests.settings')
django.setup()

import pandas as pd
import random
from django.core.management import BaseCommand
from django.db import transaction
from django.conf import settings
from tqdm import tqdm
from gigachat import GigaChat
from gigachat.exceptions import GigaChatException
from complaints.models import Complaint
from clusters.instances import gigachat_token

class Command(BaseCommand):
    help = "Load complaint data from CSV file into database with embeddings generation"

    DEFAULT_CHUNK_SIZE = 50
    # Minimum batch size before switching to individual processing
    MIN_BATCH_SIZE = 1

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv_path',
            type=str,
            default=r"D:\test_data.csv",
            help='Absolute path to CSV file with complaints data'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=self.DEFAULT_CHUNK_SIZE,
            help=f'Number of records per batch (default: {self.DEFAULT_CHUNK_SIZE})'
        )

    def handle(self, *args, **options):
        Complaint.objects.all().delete()

        csv_path = options['csv_path']
        chunk_size = options['chunk_size']

        # Проверка существования файла
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        try:
            self._process_file(csv_path, chunk_size)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Fatal error: {str(e)}"))
            raise

    def _init_gigachat(self):
        """Инициализация клиента GigaChat"""
        return GigaChat(
            credentials=gigachat_token,
            verify_ssl_certs=False,
            timeout=30
        )

    def _process_file(self, csv_path, chunk_size):
        """Основной процесс обработки файла"""
        try:
            with transaction.atomic():
                self._process_chunks(csv_path, chunk_size)
        except pd.errors.EmptyDataError:
            self.stderr.write(self.style.ERROR("CSV file is empty or corrupted"))
        except pd.errors.ParserError:
            self.stderr.write(self.style.ERROR("CSV parsing error"))

    def _process_chunks(self, csv_path, chunk_size):
        """Обработка файла чанками"""
        total_rows = self._count_rows(csv_path)
        chunks = pd.read_csv(csv_path, chunksize=chunk_size)

        with tqdm(total=total_rows, desc="Processing complaints") as progress_bar:
            giga_client = self._init_gigachat()

            for chunk in chunks:
                processed_count = self._process_batch(chunk, giga_client)
                progress_bar.update(processed_count)
        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {progress_bar.n} complaints"
        ))

    def _count_rows(self, file_path):
        """Эффективный подсчёт строк в CSV"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f) - 1  # Исключаем заголовок

    def _process_batch_with_resize(self, complaints, texts, giga_client):
        """Process a batch with automatic resizing on errors"""
        if not complaints:
            return 0
            
        # Base case: Individual processing when batch size is 1
        if len(complaints) <= self.MIN_BATCH_SIZE:
            processed_count = 0
            for complaint, text in zip(complaints, texts):
                try:
                    complaint.call_gigachat_embeddings(text, giga_client)
                    complaint.save()
                    processed_count += 1
                except Exception as e:
                    pass
            return processed_count
            
        try:
            # Try to process the entire batch
            processed_complaints = Complaint.batch_process_embeddings(
                complaints=complaints,
                texts=texts,
                giga_client=giga_client
            )
            # Save to database
            Complaint.objects.bulk_create(processed_complaints, batch_size=len(processed_complaints))
            return len(processed_complaints)
            
        except GigaChatException as e:
            # Silent splitting - no warnings
            # Split the batch in half
            mid = len(complaints) // 2
            first_half_count = self._process_batch_with_resize(complaints[:mid], texts[:mid], giga_client)
            second_half_count = self._process_batch_with_resize(complaints[mid:], texts[mid:], giga_client)
            
            return first_half_count + second_half_count
    
    def _process_batch(self, chunk, giga_client):
        """Обработка пакета записей с батчевой генерацией эмбеддингов"""
        complaints = []
        texts = []
        skipped_count = 0
        
        # Подготовка данных для батча
        for _, row in chunk.iterrows():
            try:
                if not row['Text'] or not isinstance(row['Text'], str):
                    self.stderr.write(self.style.WARNING(
                        f"Skipping complaint {row.get('Id')}: Empty or invalid text"
                    ))
                    skipped_count += 1
                    continue
                
                complaint = Complaint(
                    email=row['email'],
                    name=str(row['Id']),
                    text=row['Text'],
                    x=random.randint(0, 100),
                    y=random.randint(0, 100))
                
                complaints.append(complaint)
                texts.append(row['Text'])
                
            except Exception as e:
                self.stderr.write(self.style.WARNING(
                    f"Skipping complaint {row.get('Id')}: {str(e)}"
                ))
                skipped_count += 1
        
        # Process the batch with automatic resizing
        processed_count = self._process_batch_with_resize(complaints, texts, giga_client)
        return processed_count