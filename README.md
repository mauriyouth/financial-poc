# AI FINANCIAL SERVICES


Modules: 
    modules should be isolated technoligie usage. (docling, parser)
    No data persistance. no extrernal connections

Core/configurations:
    use pydentic settings to create objects with environment variables.
Core/dependencies:
    all dependencies should be build in this folder

Modules:
    application capablity for example parsing, chunking, retreival ...
Models:
    All pydantic models that are shared between different part of the code should go here

Services:
    service should contain the business logic: using store; modules; connectors to do a job

