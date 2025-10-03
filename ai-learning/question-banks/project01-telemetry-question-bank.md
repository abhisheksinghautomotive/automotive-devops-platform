# Project 01: Telemetry Platform Socratic Question Bank

> Fill in your answers under each `Your Answer:` block. You can iterate—add versions like V1, V2 as you refine thinking.
> Keep language simple first; we can formalize later for interview storytelling.

---
## 1. Problem Framing & Scope
**Q1.1** What does a single vehicle telemetry message contain (fields + approximate size)?  
Your Answer: I am not aware of a telemetry message contains. Please let me know

**Q1.2** Which messages must be near real-time vs can tolerate delay?  
Your Answer: Critical messages like engine information, brake information must be near real-time and messages like infotainment messages can tolerate delay.

**Q1.3** What is the smallest set of components needed for an MVP (cost first)?  
Your Answer: I don't know what is an MVP so i cannot answer that.

**Q1.4** How would you define success for the MVP (one metric + one qualitative outcome)?  
Your Answer: I don't know what is an MVP so i cannot answer that.

---
## 2. Throughput & Load
**Q2.1** Given 10,000 vehicles sending every 200ms, how many messages per second? Show math.  
Your Answer: 50,000 (10,000 x (1000/200))

**Q2.2** If each message ~150B, what data volume per minute?  
Your Answer: 450,000,000 bytes

**Q2.3** What events could cause spikes, and how might you buffer cheaply?  
Your Answer: Malfunction in vehicle, and i don't know how i can buffer cheaply.

**Q2.4** What happens to costs if message size doubles? Which layers feel it first?  
Your Answer: Cost will increase? database i guess.

---
## 3. Ingestion & Rate Limiting
**Q3.1** Why use a queue instead of writing directly to a database?  
Your Answer: I don't know

**Q3.2** What does rate limiting protect the system from (give 2 examples)?  
Your Answer: Cost savings and stable system

**Q3.3** For low cost: start with SQS + batch consumers or Kinesis stream? Why?  
Your Answer: I don't know

**Q3.4** How could you simulate message priority with basic services?  
Your Answer: I don't know

---
## 4. Data Structures (DSA Mapping)
**Q4.1** Explain a sliding window in plain words + a tiny example.  
Your Answer: i don't know

**Q4.2** How can a hash map help with duplicate detection?  
Your Answer: hash created are unique to a particular data and thus can help in duplication.

**Q4.3** Best structure to hold last 60 seconds of values per vehicle (memory aware)?  
Your Answer: dictionary

**Q4.4** When would a ring buffer be better than a dynamic list here?  
Your Answer: i don't know

---
## 5. Storage Strategy
**Q5.1** One example of hot storage vs cold storage for this project.  
Your Answer: i don't know

**Q5.2** Simplest partition key or prefix design for object storage (include time).  
Your Answer: i don't know

**Q5.3** When would you rehydrate cold data back into hot path?  
Your Answer:i don't know

**Q5.4** How long should we retain raw vs aggregated? (Initial guess)  
Your Answer: i don't know

---
## 6. Cost Awareness
**Q6.1** Which pipeline stage likely becomes most expensive first?  
Your Answer: i don't know

**Q6.2** One easy early cost optimization without hurting reliability.  
Your Answer: i don't know

**Q6.3** Trade-off of larger batch size vs latency?  
Your Answer: i don't know

**Q6.4** What metric would you track weekly to ensure cost efficiency?  
Your Answer: i don't know

---
## 7. Reliability & Resilience
**Q7.1** Define a dead-letter queue in your own words.  
Your Answer: i don't know

**Q7.2** What should happen to a partially processed message after a failure?  
Your Answer: i don't know

**Q7.3** How can retries cause duplicates?  
Your Answer: i don't know

**Q7.4** One simple health check for ingestion service.  
Your Answer: i don't know

---
## 8. Monitoring & Observability
**Q8.1** Three starter metrics to monitor first.  
Your Answer: i don't know

**Q8.2** Difference between processing time and end-to-end latency.  
Your Answer: i don't know

**Q8.3** How would you approximate end-to-end latency cheaply?  
Your Answer: i don't know

**Q8.4** First alert you would configure (and threshold).  
Your Answer: i don't know

---
## 9. Security & Access
**Q9.1** Why require auth (API key / token) for vehicles?  
Your Answer: i don't know

**Q9.2** What is encryption in transit (your words)?  
Your Answer: i don't know

**Q9.3** Easiest way to rotate an API key without downtime.  
Your Answer: i don't know

**Q9.4** One least-privilege rule for storage access.  
Your Answer: i don't know

---
## 10. Interview Story Foundations
**Q10.1** Which area do you feel strongest in today?  
Your Answer: i will answer this at the very end

**Q10.2** Which area feels weakest?  
Your Answer: i will answer this at the very end

**Q10.3** Draft 1 sentence “cost optimization” story (even hypothetical).  
Your Answer: i will answer this at the very end

**Q10.4** One architectural trade-off you want to explore deeper.  
Your Answer: i will answer this at the very end

---
## 11. Reflection & Iteration Log
Use this section to version your thinking as you learn.

| Date | Section Updated | Change Summary | Why Changed |
|------|-----------------|----------------|-------------|
| YYYY-MM-DD | Qx.y | Initial draft | Starting point |
| YYYY-MM-DD | Qx.y | Refined answer | After reading docs |

---
## 12. Next Step After Filling
1. Commit this file.
2. Let the AI review with targeted feedback.
3. Use feedback to create: MVP architecture sketch + ADR 0001.

---
*Tip: Simple, honest answers now > over-polished guesses. We’ll iterate.*
