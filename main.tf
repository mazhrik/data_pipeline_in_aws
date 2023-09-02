provider "aws" {
  region = "us-west-2"
}



# Create an IAM role for Lambda execution
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}


# Attach a policy to the IAM role (e.g., for S3 access)
resource "aws_iam_policy_attachment" "lambda_role_attachment" {
  name       = "lambda_role_attachment"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"  # Adjust the policy as needed
}


# Create an S3 bucket for data storage
resource "aws_s3_bucket" "example_bucket" {
  bucket = "myuniquebucketfortest12345"
}

# Create a Lambda function for data optimization
resource "aws_lambda_function" "data_optimization" {
  function_name = "data-optimization-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "data_optimization.lambda_handler"
  runtime       = "python3.8"
  filename      = "scripts/data_optimization.zip"

  timeout = 300  # 5 minutes in seconds
  // Other configuration options here
}


# Configure S3 event notification to trigger Lambda function
resource "aws_s3_bucket_notification" "data_bucket_notification" {
  bucket = aws_s3_bucket.example_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_optimization.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

# Grant S3 bucket permission to invoke the Lambda function
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_optimization.function_name
  principal     = "s3.amazonaws.com"

  source_arn = aws_s3_bucket.example_bucket.arn
}




resource "aws_iam_role_policy_attachment" "lambda_role_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"  # Include your existing policies here
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_policy" "quicksight_policy" {
  name = "quicksight-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
         Action = [
          "quicksight:*"
        ],
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}



resource "aws_iam_policy" "lambda_sns_publish_policy" {
  name = "lambda_sns_publish_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "sns:Publish"
        ],
        Effect   = "Allow",
        Resource = aws_sns_topic.notification_topic.arn
      }
    ]
  })
}

resource "aws_iam_policy_attachment" "lambda_sns_publish_attachment" {
  name       = "lambda-sns-publish-attachment"
  policy_arn = aws_iam_policy.lambda_sns_publish_policy.arn
  
  roles      = [aws_iam_role.lambda_role.name]
}


resource "aws_iam_role_policy_attachment" "quicksight_role_policy_attachment" {
  policy_arn = aws_iam_policy.quicksight_policy.arn
  role       = aws_iam_role.lambda_role.name
}

# Create an SNS topic
resource "aws_sns_topic" "notification_topic" {
  name = "CSVReportSavedTopic"
}



# Subscribe an email to the SNS topic
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.notification_topic.arn
  protocol  = "email"
  endpoint  = "malikmuneeb989000@gmail.com"  # Replace with your email address
}

# Output the SNS topic ARN for reference
output "sns_topic_arn" {
  value = aws_sns_topic.notification_topic.arn
}