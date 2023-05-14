FROM python:3.10-slim

RUN apt update && apt install -y git curl nano

WORKDIR /app
COPY Pipfile Pipfile.lock ./

# Install the dependencies (must still happen as root).
RUN pip install pip pipenv --upgrade
RUN pipenv install --system
RUN pip install ipython

COPY src ./src

# Create non-root users and drop permissions.
RUN groupadd -g 1000 app && useradd -g 1000 -u 1000 app
USER app

# Start the application by default.
CMD ["python", "-m", "src.main"]
