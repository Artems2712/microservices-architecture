Принцип работы сервиса:
1. Orchestrator положит в Outbox сообщение PaymentRequest.
2. Outbox Processor опубликует событие в RabbitMQ.
3. Payment Service получит сообщение, проведёт “оплату” и опубликует PaymentCompleted.
4. Orchestrator Service, получив PaymentCompleted, отдаст в Outbox событие NotificationRequest.
5. Notification Service получит запрос, отправит уведомление, опубликует NotificationCompleted.
6. Orchestrator зафиксирует “Процесс завершён” (в логах).

ИТОГ
1. Реализованы 3 микросервиса + 1 сервис-оркестратор (всего 4).
2. Все сервисы общаются через RabbitMQ.
3. В Orchestrator Service использован паттерн Outbox для надёжной публикации событий во внешнюю очередь.
4. Использован паттерн "оркестрация": есть единый координирующий сервис (Orchestrator), который определяет логику процесса (последовательность шагов) и реагирует на события от других сервисов, публикуя последующие команды
