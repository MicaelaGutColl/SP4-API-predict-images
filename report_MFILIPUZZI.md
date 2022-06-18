# Stress test report (and with scaled services)
Using Locust, an open source load testing tool.
Our goal was to determine the number of concurrent users and response times that our customer’s application could handle. This would help us understand the bottlenecks and capabilities of the page speed, scalability and stability of the web app.

## Specs:
MacBook Pro (Retina, 13-inch, Early 2015)
2,7 GHz Intel Core i5 de dos núcleos
8 GB 1867 MHz DDR3
Intel Iris Graphics 6100 1536 MB

### Test services
After completing the file `locustfile.py`, the first test was performed with LOCUST.
- 0.6 RPS
- 0.2 Failures/s
- 70192 ms average response speed
The response time statistic 100%ile (ms) was 145000 (aggregated).
All the failure occurrences (32) where due to "remote end closed connection without response", during POST/predict.

### Test scaled services
SCALED
Then, more instances were launched using `--scale SERVICE=NUM` when running `docker-compose up`.
The model service was scaled to 2 instances to check the performance with locust.
- 2.0 RPS
- 0.1 Failures/s
- 47915 ms average response speed
The response time statistic 100%ile (ms) was 98000 (aggregated).
All the failure occurrences (18) where due to "remote end closed connection without response", during POST/predict.

## Conclusions
The Average response time measures the average amount of time that passes between a client’s initial request and the last byte of a server’s response, including the delivery of HTML, images, CSS, JavaScript, and any other resources. It’s the most accurate standard measurement of the actual user experience.
In this case, we were able to reduce this by 30% when scaling services by 2.

Error rates (failures) measure the percentage of problematic requests compared to total requests. It’s not uncommon to have some errors with a high load, but obviously, error rates should be minimized to optimize the user experience.
We were able to reduce by 50% when scaling services by 2.

Requests per second measures the raw number of requests that are being sent to the server each second, including requests for HTML pages, CSS stylesheets, XML documents, JavaScript files, images, and other resources.
We were able to x3 the RPS when scaling services by 2.