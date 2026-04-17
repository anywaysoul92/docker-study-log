🐳 Docker & FastAPI Study Log
Docker의 아키텍처 이해와 FastAPI 서버 배포 과정에서의 환경 격리 및 네트워크 설정 트러블슈팅을 정리한 학습 기록입니다.

Tech Stack

Framework: FastAPI
Database: MySQL 8.0
Message Broker: Redis
Infrastucture: Docker, Docker Compose

Service Isolation: API 서버와 비동기 작업을 수행하는 Worker를 분리하여 시스템 부하를 분산했습니다.
Data Persistence: Docker Volume(local_db)을 활용하여 컨테이너 재시작 시에도 DB 데이터가 유지되도록 설계했습니다.
Network Strategy: 각 컨테이너는 Docker 내부 네트워크를 통해 서비스명(예: db, redis)으로 통신하며, 호스트와의 포트 충돌을 방지하기 위해 MySQL 외부 포트를 33061로 매핑했습니다.

worker의 수를 확장하여 특정 워커의 장애 시에도 서비스가 중단되지 않도록 가용성을 확보하는 실습을 진행하였습니다.
