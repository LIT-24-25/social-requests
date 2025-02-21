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

class Command(BaseCommand):
    help = "Load complaint data from CSV file into database with embeddings generation"

    DEFAULT_CHUNK_SIZE = 500

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path',
            type=str,
            default=r'C:\Users\new_p\Рабочий стол\project\data.csv',  # Путь по умолчанию
            help='Absolute path to CSV file with complaints data'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=self.DEFAULT_CHUNK_SIZE,
            help=f'Number of records per batch (default: {self.DEFAULT_CHUNK_SIZE})'
        )

    def handle(self, *args, **options):
        self._validate_environment()

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

    def _validate_environment(self):
        """Проверка необходимых настроек"""
        if not hasattr(settings, 'GIGACHAT_TOKEN'):
            raise ImproperlyConfigured("GIGACHAT_TOKEN not found in settings")

    def _init_gigachat(self):
        """Инициализация клиента GigaChat"""
        return GigaChat(
            credentials=settings.GIGACHAT_TOKEN,
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
                self._process_batch(chunk, giga_client, progress_bar)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {progress_bar.n} complaints"
        ))

    def _count_rows(self, file_path):
        """Эффективный подсчёт строк в CSV"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f) - 1  # Исключаем заголовок

    def _process_batch(self, chunk, giga_client, progress_bar):
        """Обработка пакета записей"""
        batch = []
        for _, row in chunk.iterrows():
            try:
                complaint = self._create_complaint(row, giga_client)
                batch.append(complaint)
                progress_bar.update(1)
            except GigaChatException as e:
                self.stderr.write(self.style.WARNING(
                    f"Skipping complaint {row.get('Id')}: {str(e)}"
                ))

        Complaint.objects.bulk_create(batch, batch_size=len(batch))

    def _create_complaint(self, row, giga_client):
        """Создание объекта Complaint с валидацией"""
        complaint = Complaint(
            email=row['email'],
            name=str(row['Id']),
            text=row['Text'],
            x=random.randint(0, 100),
            y=random.randint(0, 100))

        # Явный вызов генерации эмбеддингов
        complaint.call_gigachat_embeddings(giga_client)
        return complaint