import numpy as np
from django.core.management import BaseCommand
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from complaints.models import Complaint
from clusters.models import Cluster
from projects.models import Project
from tqdm import tqdm
import logging
from collections import Counter

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
        parser.add_argument(
            '--model',
            type=str,
            default='GigaChat',
            help='Model to use for generating cluster summaries (OpenRouter or GigaChat)'
        )
        parser.add_argument(
            '--show-sizes',
            action='store_true',
            help='Show detailed cluster size information during processing'
        )
        parser.add_argument(
            '--project-id',
            type=int,
            help='ID of the project to cluster complaints for'
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        logger.info("Starting K-Means clustering process...")
        batch_size = options['batch_size']
        project_id = options.get('project_id')
        
        # Получаем объект проекта, если project_id указан
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                logger.info(f"Clustering complaints for project ID: {project_id}")
            except Project.DoesNotExist:
                logger.error(f"Project with ID {project_id} does not exist!")
                return
        else:
            logger.info("Clustering all complaints across all projects")
        
        # Установка значения по умолчанию для show_sizes, если не указано
        if 'show_sizes' not in options:
            options['show_sizes'] = False

        # Получение данных с фильтрацией по project, если указан
        complaints_query = Complaint.objects.exclude(embedding__isnull=True)
        if project:
            complaints_query = complaints_query.filter(project=project)
            
        total = complaints_query.count()

        if total == 0:
            logger.error("No complaints with embeddings found!")
            return

        # Подготовка эмбеддингов
        embeddings = []
        valid_complaints = []
        for complaint in complaints_query.iterator():
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

        # Создание кластеров в БД с учетом project_id
        clusters = {}
        logger.info("Creating clusters")
        for label in unique_labels:
            cluster_name = f"KMeans_Cluster_{label}"
            cluster_defaults = {
                'summary': f"K-Means cluster {label}",
            }
            
            # Добавляем project в defaults, если project указан
            if project:
                cluster_defaults['project'] = project
                
            # Дополнительный фильтр для update_or_create при создании кластеров
            filter_kwargs = {'name': cluster_name}
            if project:
                filter_kwargs['project'] = project
                
            cluster, created = Cluster.objects.update_or_create(
                **filter_kwargs,
                defaults=cluster_defaults
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
            
        # Подсчет размера кластеров
        logger.info("Counting cluster sizes...")
        cluster_sizes = Counter(labels)
        for label, size in cluster_sizes.items():
            if label in clusters:
                clusters[label].size = size
                if options['show_sizes']:
                    logger.info(f"Cluster {label} size: {size}")
        
        # Сохранение обновленных размеров кластеров
        for cluster in clusters.values():
            cluster.save()
            
        # Генерация имени и описания для каждого кластера
        logger.info("Generating cluster summaries...")
        for label, cluster in clusters.items():
            try:
                # Получаем модель из опций командной строки
                model = options['model']
                response = cluster.generate_summary(model)
                
                # Обработка результата - метод может вернуть кортеж (имя, описание) или только описание
                if isinstance(response, tuple):
                    name, summary = response[0], response[1]
                    cluster.name = name 
                    cluster.summary = summary
                    if len(response) > 2:
                        cluster.model = response[2]
                else:
                    raise ValueError(f"Invalid response from generate_summary: {response}")
                
                cluster.save()
                
                logger.info(f"Generated summary for cluster {label}: {cluster.name} (size: {cluster.size})")
            except Exception as e:
                logger.warning(f"Failed to generate summary for cluster {label}: {str(e)}")
                # Используем значения по умолчанию в случае ошибки
                cluster.name = f"KMeans_Cluster_{label}"
                cluster.summary = f"K-Means cluster {label} (auto-generated)"
                cluster.save()

        # Вывод статистики по кластерам
        logger.info("Clustering statistics:")
        
        # Проверка соответствия размеров кластеров с данными в БД
        if options['show_sizes']:
            logger.info("Verifying cluster sizes with database...")
            for label, cluster in clusters.items():
                db_count = Complaint.objects.filter(cluster=cluster).count()
                if db_count != cluster.size:
                    logger.warning(f"Cluster {label} size mismatch: stored={cluster.size}, actual={db_count}")
                    # Обновляем размер кластера, если есть расхождение
                    cluster.size = db_count
                    cluster.save()
        
        # Расчет итоговой статистики
        total_assigned = sum(cluster.size for cluster in clusters.values())
        for label, cluster in sorted(clusters.items()):
            percentage = (cluster.size / total_assigned * 100) if total_assigned > 0 else 0
            logger.info(f"Cluster {label} ({cluster.name}): {cluster.size} complaints ({percentage:.1f}%)")
        
        logger.info(f"Total complaints assigned to clusters: {total_assigned}")
        project_info = f" for project ID: {project_id}" if project else ""
        logger.info(f"Clustering completed successfully{project_info}!")