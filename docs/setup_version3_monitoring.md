# Guide de Configuration du Monitoring V3

## Vue d'Ensemble

Le système de monitoring V3 combine:
- **Dashboard Plotly V2** (conservé): Monitoring intégré à l'application
- **Grafana + Prometheus** (nouveau): Monitoring externe professionnel
- **Discord Alerts** (nouveau): Notifications en temps réel

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  ┌─────────────┐         ┌───────────────────────┐     │
│  │  FastAPI    │────────▶│  PostgreSQL (V2)      │     │
│  │  (src/api)  │         │  - Prédictions        │     │
│  │             │         │  - Feedback RGPD      │     │
│  └──────┬──────┘         └───────────────────────┘     │
│         │                                                │
│         │ /metrics                                       │
│         ▼                                                │
│  ┌─────────────┐                                        │
│  │ Prometheus  │────────▶ Règles d'Alerting             │
│  │  Metrics    │                                        │
│  └──────┬──────┘                                        │
│         │                                                │
│         ▼                                                │
│  ┌─────────────┐         ┌───────────────────────┐     │
│  │   Grafana   │────────▶│   Discord Webhook     │     │
│  │  Dashboards │         │   (Notifications)     │     │
│  └─────────────┘         └───────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 1. Configuration Discord

### Créer un Webhook Discord

1. Ouvrir Discord et accéder à votre serveur
2. Paramètres du serveur → Intégrations → Webhooks
3. Cliquer sur "Nouveau Webhook"
4. Configurer:
   - **Nom**: MLOps CV Bot
   - **Canal**: #monitoring ou #alerts
   - **Avatar**: Optionnel
5. Copier l'URL du webhook
6. Ajouter dans `.env`:
```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

### Tester le Webhook
```python
# Test rapide depuis Python
from src.monitoring.discord_notifier import notifier

notifier.send_alert(
    title="Test de Configuration",
    message="Le monitoring V3 est opérationnel ! 🚀",
    level="info"
)
```

## 2. Configuration Grafana

### Premier Accès

1. Ouvrir http://localhost:3000
2. Connexion:
   - **Username**: admin
   - **Password**: (défini dans `.env` via `GRAFANA_PASSWORD`)
3. Changer le mot de passe si demandé

### Importer le Dashboard

**Méthode 1: Automatique (Provisioning)**
- Le dashboard est auto-chargé depuis `monitoring/grafana/dashboards/`
- Visible dans: Dashboards → Browse

**Méthode 2: Manuelle**
1. Dashboards → Import
2. Upload JSON file: `monitoring/grafana/dashboards/cv_dashboard.json`
3. Sélectionner les datasources:
   - Prometheus: Prometheus
   - PostgreSQL: PostgreSQL
4. Click Import

### Configurer les Alertes Discord

1. Dans Grafana: Alerting → Contact points
2. Cliquer "New contact point"
3. Configuration:
   - **Name**: Discord Alerts
   - **Integration**: Discord
   - **Webhook URL**: (copier depuis `.env`)
4. Test → Save

## 3. Prometheus

### Accès

- URL: http://localhost:9090
- Pas d'authentification par défaut

### Requêtes Utiles
```promql
# Taux de prédictions par seconde
rate(cv_predictions_total[5m])

# Latence médiane
histogram_quantile(0.50, rate(cv_inference_time_seconds_bucket[5m]))

# Pourcentage de chats prédits
sum(rate(cv_predictions_total{result="cat"}[5m])) 
  / 
sum(rate(cv_predictions_total[5m]))

# Feedbacks négatifs récents
rate(cv_user_feedback_total{satisfaction="unsatisfied"}[10m])
```

### Vérifier les Règles d'Alerte

1. Status → Rules
2. Voir les alertes actives/pending
3. Vérifier les seuils configurés dans `monitoring/prometheus/rules/alerts.yml`

## 4. Monitoring Dual (V2 + V3)

### Dashboard Plotly V2 (Existant)
- **URL**: http://localhost:8000/monitoring
- **Source**: PostgreSQL direct
- **Avantages**: Intégré, simple, sans dépendance externe
- **Contenu**:
  - Statistiques temps d'inférence
  - Satisfaction utilisateur
  - Graphiques historiques

### Dashboard Grafana V3 (Nouveau)
- **URL**: http://localhost:3000
- **Sources**: Prometheus + PostgreSQL
- **Avantages**: Temps réel, alerting, dashboards professionnels
- **Contenu**:
  - Métriques temps réel
  - Alertes configurables
  - Corrélations multi-sources

**Recommandation**: Utiliser les deux en parallèle pendant la transition

## 5. Métriques Disponibles

### Métriques Prometheus (Temps Réel)

| Métrique | Type | Description |
|----------|------|-------------|
| `cv_predictions_total` | Counter | Nombre total de prédictions par résultat |
| `cv_inference_time_seconds` | Histogram | Distribution des temps d'inférence |
| `cv_model_confidence` | Histogram | Distribution de la confiance du modèle |
| `cv_user_feedback_total` | Counter | Feedbacks utilisateurs par satisfaction |
| `cv_database_connected` | Gauge | Statut connexion BD (1=OK, 0=KO) |

### Données PostgreSQL (Historique)
```sql
-- Table existante V2: monitoring
SELECT 
    created_at,
    prediction_result,
    proba_cat,
    proba_dog,
    inference_time_ms,
    user_feedback,
    rgpd_consent
FROM monitoring
ORDER BY created_at DESC;
```

## 6. Troubleshooting

### Prometheus ne voit pas les métriques

```bash
# Vérifier que ENABLE_PROMETHEUS=true dans .env
cat .env | grep ENABLE_PROMETHEUS

# Tester l'endpoint /metrics
curl http://localhost:8000/metrics

# Vérifier les logs Prometheus
docker logs cv_prometheus --tail 50
```

### Grafana ne se connecte pas à PostgreSQL

```bash
# Vérifier la connexion depuis le container
docker exec -it cv_grafana psql -h postgres -U postgres -d predictions_feedback

# Vérifier les datasources
# Vérifier les datasources
docker exec -it cv_grafana curl http://localhost:3000/api/datasources

# Vérifier les logs Grafana
docker logs cv_grafana --tail 100
```

### Discord ne reçoit pas les alertes

```bash
# Tester le webhook manuellement
curl -X POST "${DISCORD_WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test de webhook depuis terminal",
    "username": "Test Bot"
  }'

# Vérifier la configuration dans le code
python -c "
from src.monitoring.discord_notifier import notifier
print(f'Discord enabled: {notifier.enabled}')
print(f'Webhook configured: {bool(notifier.webhook_url)}')
"

# Envoyer une alerte de test
python -c "
from src.monitoring.discord_notifier import alert_deployment_success
alert_deployment_success('test-v3.0.0')
"
```