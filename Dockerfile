FROM python:3.11-alpine3.19

COPY ./backend/ /backend/

# COPY ./entry.sh /app/

# RUN chmod +x /app/entry.sh

WORKDIR /backend/

ENV VIRTUAL_ENV=/opt/venv
ENV PYTHONPATH="/backend:$PYTHONPATH"

RUN python3 -m venv ${VIRTUAL_ENV} && . ${VIRTUAL_ENV}/bin/activate && \
  pip install --upgrade pip && \
  pip install "poetry==1.8"  && \
  poetry run pip install 'setuptools==65.5.1' && \
  poetry install

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

EXPOSE 80

# ENTRYPOINT ["source", "/app/.venv/bin/activate"]

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--lifespan", "on"]
