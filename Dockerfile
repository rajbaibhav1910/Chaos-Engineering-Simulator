FROM python:3.12-slim

WORKDIR /app

COPY chaos_sim.py README.md ./

# Default run (can be overridden with docker run args)
ENTRYPOINT ["python", "chaos_sim.py"]
CMD ["--compare", "--requests", "200", "--failure-rate", "0.3"]
