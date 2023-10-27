FROM python:3.12-alpine

RUN pip install --no-cache-dir do-problem-solving

CMD ["dops", "--help"]
