import numpy as np
from sklearn.manifold import TSNE
from django.core.management import BaseCommand
from tqdm import tqdm
from complaints.models import Complaint
import logging

logger = logging.getLogger(__name__)


def calculate_tsne(embeddings, step=500):
    """Применяет t-SNE к эмбеддингам"""
    tsne = TSNE(
        n_components=2,
        perplexity=30,
        n_iter=step,
        random_state=42,
        verbose=0
    )
    return tsne.fit_transform(np.array(embeddings))


class Command(BaseCommand):
    help = "Apply t-SNE to complaint embeddings and save coordinates"

    def add_arguments(self, parser):
        parser.add_argument(
            '--step',
            type=int,
            default=500,
            help='Number of iterations for t-SNE optimization'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process at once'
        )

    def handle(self, *args, **options):
        step = options['step']
        batch_size = options['batch_size']

        # Получаем только жалобы с эмбеддингами
        queryset = Complaint.objects.exclude(embedding__isnull=True)
        total = queryset.count()

        if total == 0:
            logger.warning("No complaints with embeddings found!")
            return

        logger.info(f"Processing {total} complaints with t-SNE...")

        # Загружаем и фильтруем эмбеддинги
        valid_embeddings = []
        valid_indices = []
        for i, complaint in enumerate(queryset.iterator()):
            try:
                # Проверяем, что эмбеддинг является списком чисел
                if isinstance(complaint.embedding, list) and all(
                        isinstance(x, (int, float)) for x in complaint.embedding):
                    valid_embeddings.append(complaint.embedding)
                    valid_indices.append(i)
            except Exception as e:
                logger.warning(f"Skipping complaint {complaint.id}: {str(e)}")

        if not valid_embeddings:
            logger.error("No valid embeddings found!")
            return

        logger.info(f"Found {len(valid_embeddings)} valid embeddings")

        # Вычисляем t-SNE
        tsne_results = calculate_tsne(valid_embeddings, step)

        # Обновляем записи батчами
        with tqdm(total=len(valid_indices), desc="Updating coordinates") as pbar:
            for i in range(0, len(valid_indices), batch_size):
                batch_indices = valid_indices[i:i + batch_size]
                batch = list(queryset.filter(id__in=[queryset[j].id for j in batch_indices]))
                for j, complaint in enumerate(batch):
                    complaint.x = tsne_results[i + j][0]
                    complaint.y = tsne_results[i + j][1]

                Complaint.objects.bulk_update(batch, ['x', 'y'])
                pbar.update(len(batch))

        logger.info("Successfully updated coordinates!")