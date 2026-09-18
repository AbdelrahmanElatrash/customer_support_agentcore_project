# AgentCore CodeBuild PROVISIONING → STOPPED

when exexut agentcore deploy , deployment field in phase
CodeBuild
  SUBMITTED    → SUCCEEDED
  QUEUED       → SUCCEEDED
  PROVISIONING → STOPPED
  BUILD        → never reached

  no build log from cloud watch 
  so analyse issue with gpt AI  and test diferent configuration
  discover the issue was BUILD_GENERAL1_MEDIUM not allowd
  suliotion is  edit file in AgentCore Starter Toolkit backages to BUILD_GENERAL1_SMALL
  .venv/lib/python3.13/site-packages/bedrock_agentcore_starter_toolkit/services/codebuild.py

  

  Tool #1: calculate_loyalty_discount
### Loyalty Discount Breakdown (Gold Member)

- **Order total:** $150.00  
- **Customer tier:** Gold  
- **Loyalty points available:** 4,250  

#### Discounts Applied

1. **Tier discount (Gold):**  
   - Rate: 10 %  
   - Discount amount: **$15.00**  

2. **Points discount:**  
   - Points redeemed: 4,200 points  
   - Discount amount: **$42.00**  

#### Final Totals
- **Remaining loyalty points:** 50 points  
- **Final total after discounts:** **$93.00**  

You saved a total of **$57.00** on your $150 order.### Loyalty Discount Breakdown (Gold Member)

- **Order total:** $150.00  
- **Customer tier:** Gold  
- **Loyalty points available:** 4,250  

#### Discounts Applied

1. **Tier discount (Gold):**  
   - Rate: 10 %  
   - Discount amount: **$15.00**  

2. **Points discount:**  
   - Points redeemed: 4,200 points  
   - Discount amount: **$42.00**  

#### Final Totals
- **Remaining loyalty points:** 50 points  
- **Final total after discounts:** **$93.00**  

You saved a total of **$57.00** on your $150 order.

# Part 3 — Functional Testing

Run the following test scenarios and verify the expected behaviour. Include screenshots or copy the terminal output in your submission.

### Test 1 — Order Tracking

```bash
agentcore invoke '{"prompt": "Can you track order ORD-001?", "customer_id": "CUST-123", "session_id": "t1"}'
# Expected: shipping status, tracking number TRK987654321, carrier UPS, estimated delivery
```

### Test 2 — Refund Processing

```bash
agentcore invoke '{"prompt": "I want to return my Kindle Paperwhite (ORD-002). Please initiate a refund.", "customer_id": "CUST-123", "session_id": "t2"}'
# Expected: refund ID, APPROVED status, 3-5 business days message
```

### Test 3 — Knowledge Base (RAG)

```bash
agentcore invoke '{"prompt": "What are the benefits of the Platinum loyalty tier?", "customer_id": "CUST-123", "session_id": "t3"}'
# Expected: free same-day shipping, 15% discount, priority support
```

### Test 4 — Memory (Long-Term)

```bash
# Session A — introduce yourself
agentcore invoke '{"prompt": "Hi, I am Jane. I prefer concise responses.", "customer_id": "CUST-123", "session_id": "s-A"}'

# Session B (new session) — verify recall
agentcore invoke '{"prompt": "Do you remember my name and communication preference?", "customer_id": "CUST-123", "session_id": "s-B"}'
# Expected: agent recalls "Jane" and "concise responses"
```

### Test 5 — Loyalty Discount Calculation

```bash
agentcore invoke '{"prompt": "I am a Gold member with 4250 points. Calculate my discount on a $150 standard order.", "customer_id": "CUST-123", "session_id": "t5"}'
# Expected: points redeemed, tier discount 10%, final total, remaining points
```

### Test 6 — Browser Tool

```bash
agentcore invoke '{"prompt": "Go to https://www.amazon.com and tell me the page title.", "customer_id": "CUST-123", "session_id": "t6"}'
# Expected: page title retrieved from live Amazon.com