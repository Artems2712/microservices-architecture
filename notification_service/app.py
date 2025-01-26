import os
import json
import pika
import threading
import time
from flask import Flask, jsonify

app = Flask(__name__)

RABBIT_HOST = os.environ.get("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))

NOTIFICATION_REQUEST_QUEUE = "NotificationRequest"
NOTIFICATION_COMPLETED_QUEUE = "NotificationCompleted"

def callback(ch, method, properties, body):
    """
    Обработка события NotificationRequest.
    """
    data = json.loads(body)
    order_id = data.get("order_id")
    notification_type = data.get("notification_type")
    print(f"[Notification Service] Получен запрос на уведомление: order_id={order_id}, type={notification_type}")

    # Имитируем отправку уведомления (email, sms и т.п.)
    time.sleep(2)
    print(f"[Notification Service] Уведомление отправлено!")

    # Публикуем событие NotificationCompleted
    publish_event(NOTIFICATION_COMPLETED_QUEUE, {"order_id": order_id, "result": "notified"})

    ch.basic_ack(delivery_tag=method.delivery_tag)

def publish_event(queue_name, payload):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    message = json.dumps(payload)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message
    )
    connection.close()
    print(f"[Notification Service] Опубликовали событие {queue_name}: {payload}")

def consume_notification_requests():
    """
    Подписка на очередь NotificationRequest.
    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue=NOTIFICATION_REQUEST_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=NOTIFICATION_REQUEST_QUEUE, on_message_callback=callback)
    print("[Notification Service] Ожидание сообщений в очереди NotificationRequest...")
    channel.start_consuming()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

def main():
    # Запускаем поток, который слушает очередь NotificationRequest
    t = threading.Thread(target=consume_notification_requests, daemon=True)
    t.start()

    # Запускаем Flask
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
