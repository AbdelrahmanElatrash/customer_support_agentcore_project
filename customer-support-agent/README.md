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

  