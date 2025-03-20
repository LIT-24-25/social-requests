import numpy as np
from django.core.management import BaseCommand
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from complaints.models import Complaint
from clusters.models import Cluster
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cluster complaints using K-Means algorithm"

    def add_arguments(self, parser):
        parser.add_argument(
            '--n-clusters',
            type=int,
            default=5,
            help='Number of clusters to form'
        )
        parser.add_argument(
            '--auto-clusters',
            action='store_true',
            help='Automatically determine optimal number of clusters'
        )
        parser.add_argument(
            '--max-clusters',
            type=int,
            default=15,
            help='Maximum clusters for auto-detection'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process at once'
        )
        parser.add_argument(
            '--plot',
            action='store_true',
            help='Show elbow method plot'
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        logger.info("Starting K-Means clustering process...")
        batch_size = options['batch_size']

        # Получение данных
        complaints = Complaint.objects.exclude(embedding__isnull=True)
        total = complaints.count()

        if total == 0:
            logger.error("No complaints with embeddings found!")
            return

        # Подготовка эмбеддингов
        embeddings = []
        valid_complaints = []
        for complaint in complaints.iterator():
            try:
                if isinstance(complaint.embedding, list):
                    embedding = np.array(complaint.embedding)
                    #embedding = np.array([complaint.x, complaint.y])
                    if not np.isnan(embedding).any():
                        embeddings.append(embedding)
                        valid_complaints.append(complaint)
            except Exception as e:
                logger.warning(f"Skipping complaint {complaint.id}: {str(e)}")

        if not embeddings:
            logger.error("No valid embeddings found!")
            return

        # Нормализация данных
        scaler = StandardScaler()
        scaled_embeddings = scaler.fit_transform(embeddings)
        logger.info("Embeddings normalized using StandardScaler")

        # Автоматический подбор числа кластеров
        if options['auto_clusters']:
            logger.info("Calculating optimal number of clusters...")
            wcss = []
            silhouette_scores = []
            max_clusters = min(options['max_clusters'], len(embeddings) - 1)

            for i in tqdm(range(2, max_clusters + 1)):
                kmeans = KMeans(n_clusters=i, init='k-means++', random_state=42, max_iter=1000, tol=1e-5)
                kmeans.fit(scaled_embeddings)
                wcss.append(kmeans.inertia_)
                if i > 1:
                    silhouette_scores.append(silhouette_score(scaled_embeddings, kmeans.labels_))
            print(silhouette_scores)


            # Автовыбор числа кластеров
            optimal_clusters = np.argmax([0] + silhouette_scores) + 2
            logger.info(f"Optimal number of clusters: {optimal_clusters}")
            n_clusters = optimal_clusters
        else:
            n_clusters = options['n_clusters']

        # Кластеризация
        logger.info(f"Performing K-Means clustering with {n_clusters} clusters...")
        kmeans = KMeans(
            n_clusters=n_clusters,
            init='k-means++',
            max_iter=300,
            random_state=42
        )
        labels = kmeans.fit_predict(scaled_embeddings)

        # Анализ результатов
        unique_labels = np.unique(labels)
        logger.info(f"Created {len(unique_labels)} clusters")
        logger.info(f"Silhouette Score: {silhouette_score(scaled_embeddings, labels):.2f}")

        # Создание кластеров в БД
        clusters = {}
        for label in unique_labels:
            cluster, created = Cluster.objects.update_or_create(
                name=f"KMeans_Cluster_{label}",
                defaults={'summary': f"K-Means cluster {label}"}
            )
            clusters[label] = cluster

        # Обновление жалоб
        logger.info("Updating complaints with cluster info...")
        for i in tqdm(range(0, len(valid_complaints), batch_size)):
            batch = valid_complaints[i:i+batch_size]
            label_batch = labels[i:i + batch_size]

            for complaint, label in zip(batch, label_batch):
                complaint.cluster = clusters[label]

            Complaint.objects.bulk_update(batch, ['cluster'])

        logger.info("Clustering completed successfully!")