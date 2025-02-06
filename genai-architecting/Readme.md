# Architecting Gen AI

## Architectural / Design Considerations

### Business Goals

As a Solution Architect, I am to create archietctural diagrams to help stakeholders understand key componoents of Gen AI workloads, and visualize possible technical paths and technical uncertainty when adopting Gen AI.

### Functional Requirements

The company wants to invest in owning their infrastructure. The reason is because there is a concern about the privacy of user data and also a concern that the cost of managed services for Gen AI will greatly increase. They want to invest an AI PC where they can afford 10-15K. They have 300 active students, and students are located within the city of Paris.

### Asssumptions

We are assuming that the open-source LLM that we choose will be powerful enough to run on hardware with an investment of 10-15K. We are going to hook up a single server in our office to the internet and we should have enough bandwidth to serve the 300 students.

### Data Strategy

There is a concern of copyrighted materials, so we must purhcase supply materials and store them for access in our database.

We can implement a vector database for efficient storage and retrieval of educational content, enhancing the model's context understanding.

### Infrastructure Design

We can consider a hybrid approach, using on-premises server to handle sensitive data processing and core AI operations, and leverage cloud services for scalability, data backup, and non-sensitive operations. Possibly implementing containerization for flexibility and easier management.

### Integration and Deployment

Develop RESTful APIs and interfaces for easy access to educational materials and facilitate student interactions with the AI system. Implement robust authentication to ensure only authorized access to the AI service.

We can implement CI/CD pipelines for regular updates and deployments.

### Monitoring and Optimization

We can set up logging and telemetry for model performance, response times, and usage patterns. We can also implement a system for collecting students feedback to continuously improve the AI's effectiveness.

## LLM Considerations

We plan to implement input and output guardrails around the model to ensure LLM receives and output appropriate content that aligns with course standards. In addition, we will add caching strategy to store frequently accessed information, reducing latency and computational costs.

We are considering using IBM Granite because it is an open-source model with training data that is traceable so we can avoid any copyright issues and we are able to know what is going on in the model. The IBM Granite has smaller models that might fit my hardware constraints.

https://huggingface.co/ibm-granite
