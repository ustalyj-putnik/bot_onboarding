from prometheus_client import Histogram, Counter
RAG_LATENCY = Histogram("rag_latency_seconds", "RAG end-to-end latency")
ANS_GOOD    = Counter("answer_good_total", "Positive ratings")
ANS_BAD     = Counter("answer_bad_total", "Negative ratings")