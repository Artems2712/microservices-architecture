# orchestrator_service/outbox_processor.py
import time
import json
import pika
from database import SessionLocal, OutboxEvent

RABBIT_HOST = "rabbitmq"
RABBIT_PORT = 5672

def publish_event(event_type, payload):
    """Публикация события напрямую в RabbitMQ."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    channel = connection.channel()

    # Обменник для примера не используем (или создаём), просто публикуем в очередь
    queue_name = event_type  # упростим: имя очереди = имя события
    channel.queue_declare(queue=queue_name, durable=True)

    message = json.dumps(payload)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message
    )
    connection.close()

def run_outbox_processor():
    """Запуск бесконечного цикла обработки Outbox."""
    while True:
        try:
            db = SessionLocal()
            # Выбираем все непубликованные события
            events = db.query(OutboxEvent).filter_by(published=False).all()
            for event in events:
                publish_event(event.event_type, json.loads(event.payload))
                event.published = True
                db.add(event)
            db.commit()
            db.close()
        except Exception as e:
            print("Ошибка в outbox-процессоре:", e)
        time.sleep(5)  # Периодичность проверки Outbox
