FROM maven:3.9.16-eclipse-temurin-21 as builder
LABEL authors="chaum"
WORKDIR usr/local/app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn clean package -DskipTests


FROM eclipse-temurin:21
WORKDIR /usr/local/app
COPY --from=builder /usr/local/app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]