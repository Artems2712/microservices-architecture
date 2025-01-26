# payment_service/app.py
import os
import json
import pika
import threading
import time
from flask import Flask, jsonify

app = Flask(__name__)

RABBIT_HOST = os.environ.get("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))

PAYMENT_REQUEST_QUEUE = "PaymentRequest"
PAYMENT_COMPLETED_QUEUE = "PaymentCompleted"

def callback(ch, method, properties, body):
    """
    Обработка события PaymentRequest.
    """
    data = json.loads(body)
    order_id = data.get("order_id")
    amount = data.get("amount")
    print(f"[Payment Service] Получен запрос на оплату: order_id={order_id}, amount={amount}")

    # Здесь могла бы быть реальная логика оплаты...
    time.sleep(2)  # Имитация задержки

    # Публикуем событие PaymentCompleted
    publish_event(PAYMENT_COMPLETED_QUEUE, {"order_id": order_id, "status": "success"})

    # Подтверждаем, что сообщение обработано
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
    print(f"[Payment Service] Опубликовали событие {queue_name}: {payload}")

def consume_payment_requests():
    """
    Подписка на очередь PaymentRequest и ожидание сообщений.
    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue=PAYMENT_REQUEST_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)  # Чтобы не отправлялись новые сообщения пока не ACK
    channel.basic_consume(queue=PAYMENT_REQUEST_QUEUE, on_message_callback=callback)
    print("[Payment Service] Ожидание сообщений в очереди PaymentRequest...")
    channel.start_consuming()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

def main():
    # Запустим поток, который слушает очередь
    t = threading.Thread(target=consume_payment_requests, daemon=True)
    t.start()

    # Запускаем Flask
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
