from sanic import Sanic
from sanic.response import json
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

app = Sanic(__name__)

# Подключение к MongoDB
client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client['services_db']
collection = db['services']

@app.route("/services/history/<service_name>")
async def get_service_history(request, service_name):
    # Получение истории изменения состояния сервиса по имени
    history = await collection.find({"name": service_name}).to_list(None)
    return json(history)

@app.route("/services/sla/<service_name>")
async def calculate_sla(request, service_name):
    # Расчет SLA для сервиса на указанном интервале времени
    start_date = datetime.now() - timedelta(days=7)  # Пример: последние 7 дней
    end_date = datetime.now()
    total_time = 0
    downtime = 0
    history = await collection.find({"name": service_name, "timestamp": {"$gte": start_date, "$lte": end_date}}).to_list(None)
    for entry in history:
        total_time += entry.get("duration", 0)
        if entry.get("state") == "Down":
            downtime += entry.get("duration", 0)
    if total_time == 0:
        sla_percentage = 100.0
    else:
        sla_percentage = ((total_time - downtime) / total_time) * 100
    return json({"service_name": service_name, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "sla_percentage": round(sla_percentage, 3)})

@app.route("/services/current_status")
async def get_current_status(request):
    # Получение списка сервисов и их текущих состояний
    current_statuses = await collection.distinct("name")
    return json(current_statuses)

@app.route("/services/add", methods=['POST'])
async def add_service(request):
    data = request.json
    service = {
        "name": data.get("name"),
        "state": data.get("state"),
        "description": data.get("description"),
        "timestamp": datetime.now()
    }
    result = await collection.insert_one(service)
    return json({"message": "Service added successfully", "id": str(result.inserted_id)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)