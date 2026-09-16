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
