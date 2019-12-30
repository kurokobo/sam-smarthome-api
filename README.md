# APIs for Home Automation

This repository includes:

* Line bot
    * Use as main interface
* Air Control
    * Control air conditionar throwgh Nature Remo Cloud API
* Quality of Air
    * Check current quality of air
    * Curent values are collected by EdgeX Foundry and stored in Redis

Everithing works as AWS Lambda function througth AWS API Gateway.

Ready for deploy using CloudFormation.


## Procedure

Modify following files:

* `samconfig.toml`
    * Used in `sam deploy` operation
* `env.json`
    * Used in `sam local start-api`

Then build,

```sh
sam build --use-container
```

test if you want,

```sh
sam local start-api --env-vars ./env.json
```

finally, deploy.

```sh
sam deploy
```