import numpy as np
from django.core.management import BaseCommand
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import Normalizer
from complaints.models import Complaint
from clusters.models import Cluster
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cluster complaints using DBSCAN algorithm"

    def add_arguments(self, parser):
        parser.add_argument(
            '--eps',
            type=float,
            default=0.5,
            help='Maximum distance between samples in the same neighborhood'
        )
        parser.add_argument(
            '--min-samples',
            type=int,
            default=5,
            help='Minimum number of samples in a neighborhood'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process at once'
        )
        parser.add_argument(
            '--metric',
            type=str,
            default='cosine',
            help='Distance metric to use for DBSCAN (e.g., euclidean, cosine)'
        )

    def handle(self, *args, **options):
        eps = options['eps']
        min_samples = options['min_samples']
        batch_size = options['batch_size']
        metric = options['metric']

        # Получаем все жалобы с валидными эмбеддингами
        complaints = Complaint.objects.exclude(embedding__isnull=True)
        total = complaints.count()

        if total == 0:
            logger.error("No complaints with embeddings found!")
            return

        logger.info(f"Processing {total} complaints with DBSCAN (eps={eps}, min_samples={min_samples}, metric={metric})...")

        # Подготовка данных для кластеризации
        embeddings = []
        valid_complaints = []
        for complaint in complaints.iterator():
            try:
                if isinstance(complaint.embedding, list):
                    embedding = np.array(complaint.embedding)
                    if not np.isnan(embedding).any():  # Проверка на NaN
                        embeddings.append(embedding)
                        valid_complaints.append(complaint)
            except Exception as e:
                logger.warning(f"Skipping complaint {complaint.id}: {str(e)}")

        if not embeddings:
            logger.error("No valid embeddings found!")
            return

        # Логгирование информации о данных
        logger.info(f"Total embeddings: {len(embeddings)}")
        logger.info(f"Embedding dimensionality: {len(embeddings[0])}")
        logger.info(f"Sample embedding: {embeddings[0]}")
        logger.info(f"Min/Max values in embeddings: {np.min(embeddings)}, {np.max(embeddings)}")

        # Нормализация эмбеддингов (для косинусного расстояния)
        normalizer = Normalizer(norm='l2')
        embeddings = normalizer.fit_transform(embeddings)

        # Кластеризация с DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric=metric)
        labels = dbscan.fit_predict(embeddings)

        # Анализ результатов
        unique_labels, counts = np.unique(labels, return_counts=True)
        logger.info(f"Clusters found: {unique_labels}")
        logger.info(f"Cluster sizes: {counts}")

        # Если все точки - шум
        if len(unique_labels) == 1 and unique_labels[0] == -1:
            logger.error("No clusters detected. Adjust parameters!")
            return

        # Создание или обновление кластеров
        clusters = {}
        for label in unique_labels:
            if label == -1:  # Пропускаем шум
                continue
            cluster, created = Cluster.objects.get_or_create(
                name=f"Cluster_{label}",
                defaults={'summary': f"Auto-generated cluster {label}"}
            )
            cluster.generate_summary("GigaChat")
            clusters[label] = cluster

        # Обновление жалоб с информацией о кластерах
        with tqdm(total=len(valid_complaints), desc="Updating clusters") as pbar:
            for i in range(0, len(valid_complaints), batch_size):
                batch = valid_complaints[i:i + batch_size]
                label_batch = labels[i:i + batch_size]

                for complaint, label in zip(batch, label_batch):
                    if label == -1:
                        complaint.cluster = None
                    else:
                        complaint.cluster = clusters.get(label)

                for complaint in batch:
                    complaint.save()
                pbar.update(len(batch))

        logger.info(f"Created {len(clusters)} clusters")
        logger.info("Cluster distribution:")
        for label, count in zip(unique_labels, counts):
            logger.info(f"Label {label}: {count} items")