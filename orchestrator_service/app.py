import threading
import json
import pika
import os
from flask import Flask, jsonify
from database import init_db, SessionLocal, OutboxEvent
from outbox_processor import run_outbox_processor

RABBIT_HOST = os.environ.get("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.environ.get("RABBIT_PORT", "5672"))

PAYMENT_COMPLETED_QUEUE = "PaymentCompleted"
NOTIFICATION_COMPLETED_QUEUE = "NotificationCompleted"

app = Flask(__name__)

def listen_payment_completed():
    """Подписка на очередь PaymentCompleted."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue=PAYMENT_COMPLETED_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        order_id = data.get("order_id")
        status = data.get("status")
        print(f"[Orchestrator] Получено PaymentCompleted: order_id={order_id}, status={status}")

        # Если оплата успешна, оркестратор инициирует NotificationRequest
        if status == "success":
            db = SessionLocal()
            outbox_entry = OutboxEvent(
                event_type="NotificationRequest",
                payload=json.dumps({"order_id": order_id, "notification_type": "email"})
            )
            db.add(outbox_entry)
            db.commit()
            db.close()

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=PAYMENT_COMPLETED_QUEUE, on_message_callback=callback)
    print("[Orchestrator] Ожидание событий PaymentCompleted...")
    channel.start_consuming()

def listen_notification_completed():
    """Подписка на очередь NotificationCompleted."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT)
    )
    channel = connection.channel()
    channel.queue_declare(queue=NOTIFICATION_COMPLETED_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        order_id = data.get("order_id")
        result = data.get("result")
        print(f"[Orchestrator] Получено NotificationCompleted: order_id={order_id}, result={result}")
        print("[Orchestrator] Процесс завершён.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=NOTIFICATION_COMPLETED_QUEUE, on_message_callback=callback)
    print("[Orchestrator] Ожидание событий NotificationCompleted...")
    channel.start_consuming()

@app.route("/start_process", methods=["POST", "GET"])
def start_process():
    """
    Запуск бизнес-процесса: генерируем PaymentRequest через Outbox.
    """
    db = SessionLocal()
    outbox_entry = OutboxEvent(
        event_type="PaymentRequest",
        payload=json.dumps({"order_id": 123, "amount": 999.0})
    )
    db.add(outbox_entry)
    db.commit()
    db.close()

    return jsonify({"message": "Process started. PaymentRequest is placed to Outbox."})

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

def main():
    init_db()

    # Запуск потоков:
    # 1) outbox-процессор
    t1 = threading.Thread(target=run_outbox_processor, daemon=True)
    t1.start()

    # 2) слушатель PaymentCompleted
    t2 = threading.Thread(target=listen_payment_completed, daemon=True)
    t2.start()

    # 3) слушатель NotificationCompleted
    t3 = threading.Thread(target=listen_notification_completed, daemon=True)
    t3.start()

    # Запускаем Flask
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
