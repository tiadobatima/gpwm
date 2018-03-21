##
## Owner: infrastrucure
##
## Dependencies: None
##
## Parameters:
##   - team (required): The team owning the stack
##   - s3_bucket(required): The S3 bucket name for the whole team.
##   - hostedzone(optional): The domain name for the team/project.
##     If specified an SSL certificate will be created, and the
##     validation e-mail will be sent to the root domain.
##
AWSTemplateFormatVersion: "2010-09-09"
Description: Team-wide resources
Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: ${s3_bucket}
      Tags:
        - {Key: team, Value: ${team}}

% if "hostedzone" in locals() and hostedzone:
  Certificate:
    Type: "AWS::CertificateManager::Certificate"
    Properties:
      DomainName: "*.${hostedzone}"
      DomainValidationOptions:
      - DomainName: "*.${hostedzone}"
        ValidationDomain: ${".".join(hostedzone.split(".")[-2:])}
      Tags: 
        - {Key: team, Value: ${team}}
% endif
