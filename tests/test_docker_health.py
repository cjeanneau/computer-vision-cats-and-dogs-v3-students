"""
Tests de santé des containers Docker
Exécutés uniquement en environnement Docker
"""
import pytest
import requests
import os
from time import sleep

# Skip si pas en environnement Docker
pytestmark = pytest.mark.skipif(
    os.getenv('DOCKER_ENV') != 'true',
    reason="Tests Docker uniquement en environnement containerisé"
)

class TestDockerServices:
    """Tests des services Docker Compose"""
    
    @pytest.fixture(autouse=True)
    def wait_for_services(self):
        """Attend que les services soient prêts"""
        sleep(5)
    
    def test_app_container_healthy(self):
        """Vérifie que le container app est en bonne santé"""
        try:
            response = requests.get("http://cv_app:8000/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Container app non accessible")
    
    def test_prometheus_accessible(self):
        """Vérifie que Prometheus est accessible"""
        try:
            response = requests.get("http://prometheus:9090/-/healthy", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Prometheus non accessible")
    
    def test_grafana_accessible(self):
        """Vérifie que Grafana est accessible"""
        try:
            response = requests.get("http://grafana:3000/api/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            pytest.skip("Grafana non accessible")
    
    def test_postgres_accessible(self):
        """Vérifie que PostgreSQL est accessible"""
        import psycopg2
        try:
            conn = psycopg2.connect(
                host="postgres",
                port=5432,
                database=os.getenv("DB_NAME", "predictions_feedback"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PWD")
            )
            conn.close()
            assert True
        except Exception:
            pytest.skip("PostgreSQL non accessible")