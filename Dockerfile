# ---------- Сборка приложения ----------
FROM gradle:8.8-jdk17-alpine AS build
WORKDIR /workspace

# Копируем проект
COPY prac_5 ./prac_5


COPY ./settings.gradle.kts ./build.gradle.kts ./
# Собираем fat-jar (без тестов)
RUN --mount=type=cache,target=/home/gradle/.gradle gradle clean bootJar -x test

# ---------- Рантайм ----------
FROM eclipse-temurin:17-jre
WORKDIR /app

# Копируем артефакт
COPY --from=build /workspace/prac_5/build/libs/*.jar /app/app.jar

# Каталог хранения файлов (по умолчанию совпадает с storage.location=uploads)
VOLUME ["/app/uploads"]

EXPOSE 8080

ENTRYPOINT ["java","-jar","/app/app.jar"]


