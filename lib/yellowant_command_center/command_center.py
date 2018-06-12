"""This file contains the logic to understand a user message request
 from YA and return a response in the format of
 a YA message object accordingly
"""
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, MessageButtonsClass
import boto3
from ..yellowant_api.models import aws, UserIntegration
import json


class CommandCenter(object):
    """Handles user commands
    Args:
        yellowant_integration_id (int): The integration id of a YA user
        self.commands (str): Invoke name of the command the user is calling
        args (dict): Any arguments required for the command to run
    """

    def __init__(self, yellowant_user_id, yellowant_integration_id, function_name,
                 args, application_invoke_name):
        self.yellowant_user_id = yellowant_user_id
        self.application_invoke_name = application_invoke_name
        self.yellowant_integration_id = yellowant_integration_id
        self.account_id = UserIntegration.objects.get(yellowant_integration_invoke_name=
                                                      self.application_invoke_name)
        self.aws_access_key = aws.objects.get(id=self.account_id).AWS_APIAccessKey
        self.aws_secret_token = aws.objects.get(id=self.account_id).AWS_APISecretAccess
        self.function_name = function_name
        self.args = args

    def parse(self):
        """The connection between yellowant commands and functions in django"""
        self.commands = {
            'list-functions': self.list_function,
            'region': self.region,
            'next-page': self.next_page,
            'invoke-async': self.invoke,
            'settings': self.settings,
            'get-logs': self.get_logs,
        }
        return self.commands[self.function_name](self.args)

    def marker(self, args, page):
        """Returns the marker of the required page No."""
        region = args['Region']
        aws_lambda = boto3.client(service_name='lambda', region_name=region,
                                  api_version=None, use_ssl=True, verify=None,
                                  endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                  aws_secret_access_key=self.aws_secret_token,
                                  aws_session_token=None, config=None)
        n = page//5
        p = int((page % 5)*10)-10
        if p == -10:
            response = aws_lambda.list_functions(MaxItems=40)
            next_marker = response['NextMarker']
            n = n-1
        elif p == 0:
            response = aws_lambda.list_functions(MaxItems=50)
            next_marker = response['NextMarker']
            n = n-1
        else:
            response = aws_lambda.list_functions(MaxItems=p)
            next_marker = response['NextMarker']
        i = 1
        for i in range(1, n+1):
            response = aws_lambda.list_functions(Marker=next_marker, MaxItems=50)
            next_marker = response['NextMarker']
            i = i+1

        return next_marker

    def list_function(self, args):
        """ Gives the list of the functions in the Lambda"""
        message = MessageClass()
        attachment = MessageAttachmentsClass()
        region = args['Region']
        # Page is an optional argument
        try:
            page = int(args["Page"])
        except:
            page = 1
        # If page no. is greater than 1 get the marker of the specified field and use it to get the functions in that page
        if page > 1:
            aws_lambda = boto3.client(service_name='lambda', region_name=region,
                                      api_version=None, use_ssl=True, verify=None,
                                      endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                      aws_secret_access_key=self.aws_secret_token,
                                      aws_session_token=None, config=None)

            #Snippet added to check the Page No. entered is valid or not
            check = aws_lambda.get_account_settings()
            max_page = int(int(check['AccountUsage']['FunctionCount'])/10)+1

            # If page no. entered is greter than max pages of the Lambda then return this
            if page > max_page:
                message.message_text = "The Page no. entered is more than the pages present"
                return message.to_json()

            next_marker = self.marker(args, page)
            response = aws_lambda.list_functions(Marker=next_marker, MaxItems=10)
            functions = [Function['FunctionName'] for Function in response['Functions']]

            # Attaching functions and thier respective Buttons
            for Function in functions:
                attachment = MessageAttachmentsClass()
                attachment.title = Function
                message.attach(attachment)

                # Button to get the logs of the function
                button = MessageButtonsClass()
                button.text = "Get Logs"
                button.value = "Get Logs"
                button.name = "Get Logs"
                button.command = {"service_application": self.yellowant_integration_id,
                                  "function_name": "get-logs",
                                  "data": {"FunctionName": Function, "Region": region}}
                attachment.attach_button(button)

                # Button to invoke the function
                button1 = MessageButtonsClass()
                button1.text = "Invoke"
                button1.value = "Invoke"
                button1.name = "Invoke"
                button1.command = {"service_application": self.yellowant_integration_id,
                                   "function_name": "invoke-async",
                                   "data": {"FunctionName": Function, "Region": region},
                                   "inputs": ["input"]}
                attachment.attach_button(button1)

            try:
                # Button to get the functions in next page, Checks actually if next page exists or not
                attachment = MessageAttachmentsClass()
                button2 = MessageButtonsClass()
                button2.text = "Next Page"
                button2.value = "Next Page"
                button2.name = "Next Page"
                button2.command = {"service_application": self.yellowant_integration_id,
                                   "function_name": "next-page",
                                   "data": {"NextMarker": response['NextMarker'], "Region": region}}
                attachment.attach_button(button2)
                message.message_text = ("The Functions in Page %d are:" % page)

            except:
                message.message_text = "This is the last page"

        # If page is 1 or not specified than return the functions in the 1st page
        else:
            aws_lambda = boto3.client(service_name='lambda', region_name=region,
                                      api_version=None, use_ssl=True, verify=None,
                                      endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                      aws_secret_access_key=self.aws_secret_token,
                                      aws_session_token=None, config=None)

            # Display first 10 functions
            response = aws_lambda.list_functions(MaxItems=10)
            functions = [Function['FunctionName'] for Function in response['Functions']]
            for Function in functions:
                attachment = MessageAttachmentsClass()
                attachment.title = Function
                message.attach(attachment)

                # Button to get the logs of the function
                button = MessageButtonsClass()
                button.text = "Get Logs"
                button.value = "Get Logs"
                button.name = "Get Logs"
                button.command = {"service_application": self.yellowant_integration_id,
                                  "function_name": "get-logs",
                                  "data": {"FunctionName": Function, "Region": region}}
                attachment.attach_button(button)

                # Button to invoke the function
                button1 = MessageButtonsClass()
                button1.text = "Invoke"
                button1.value = "Invoke"
                button1.name = "Invoke"
                button1.command = {"service_application": self.yellowant_integration_id,
                                   "function_name": "invoke-async",
                                   "data": {"Function-Name": Function, "Region": region},
                                   "inputs": ["input"]}
                attachment.attach_button(button1)

            try:
                # Button to get the functions in next page, Checks actually if next page exists or not
                attachment = MessageAttachmentsClass()
                button2 = MessageButtonsClass()
                button2.text = "Next Page"
                button2.value = "Next Page"
                button2.name = "Next Page"
                button2.command = {"service_application": self.yellowant_integration_id,
                                   "function_name": "next-page",
                                   "data": {"NextMarker": response['NextMarker'], "Region": region}}
                attachment.attach_button(button2)
                message.message_text = ("The Functions in Page %d are:" % page)

            except:
                message.message_text = "This is the last page"

        return message.to_json()

    def next_page(self, args):
        """This returns the list of functions in the next page"""
        message = MessageClass()
        region = args['Region']
        next_marker = args['NextMarker']
        aws_lambda = boto3.client(service_name='lambda', region_name=region,
                                  api_version=None, use_ssl=True, verify=None,
                                  endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                  aws_secret_access_key=self.aws_secret_token,
                                  aws_session_token=None, config=None)
        # Gets the next ten functions in lambda
        response = aws_lambda.list_functions(Marker=next_marker, MaxItems=10)
        functions = [Function['FunctionName'] for Function in response['Functions']]
        for Function in functions:

            attachment = MessageAttachmentsClass()
            attachment.title = Function

            # Button to get the logs of the function
            button = MessageButtonsClass()
            button.text = "Get Logs"
            button.value = "Get Logs"
            button.name = "Get Logs"
            button.command = {"service_application": self.yellowant_integration_id,
                              "function_name": "get-logs",
                              "data": {"FunctionName": Function, "Region": region}}
            attachment.attach_button(button)

            # Button to invoke the function
            button1 = MessageButtonsClass()
            button1.text = "Invoke"
            button1.value = "Invoke"
            button1.name = "Invoke"
            button1.command = {"service_application": self.yellowant_integration_id,
                               "function_name": "invoke-async",
                               "data": {"Function-Name": Function, "Region": region},
                               "inputs": ["input"]}
            attachment.attach_button(button1)
            message.attach(attachment)

        try:
            # Button to get the functions in next page, Checks actually if next page exists or not
            attachment = MessageAttachmentsClass()
            button2 = MessageButtonsClass()
            button2.text = "Next Page"
            button2.value = "Next Page"
            button2.name = "Next Page"
            button2.command = {"service_application": self.yellowant_integration_id,
                               "function_name": "next-page",
                               "data": {"NextMarker": response['NextMarker'], "Region": region}}
            attachment.attach_button(button2)
            message.attach(attachment)
            message.message_text = "The Functions present are:"

        except:
            message.message_text = "This is the Last page and The Functions present are: "

        return message.to_json()

    def invoke(self, args):
        """ To invoke the specified function in the background"""
        functionname = args["Function-Name"]
        input_args = json.dumps(args["input"])
        region = args['Region']
        message = MessageClass()
        # try except block to check the Arguments are compatible with function or not
        try:
            aws_lambda = boto3.client(service_name='lambda', region_name=region,
                                      api_version=None, use_ssl=True, verify=None,
                                      endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                      aws_secret_access_key=self.aws_secret_token,
                                      aws_session_token=None, config=None)
            response = aws_lambda.invoke_async(
                FunctionName=functionname,
                InvokeArgs=input_args,
            )

            message.message_text = "The Function is invoked"

        except:
            message.message_text = "The Function name and Arguments provided are incompatible :"

        return message.to_json()

    def settings(self, args):
        """ To get the number of functions in the Lambda """
        region = args['Region']
        message = MessageClass()
        aws_lambda = boto3.client(service_name='lambda', region_name=region,
                                  api_version=None, use_ssl=True, verify=None,
                                  endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                  aws_secret_access_key=self.aws_secret_token,
                                  aws_session_token=None, config=None)
        response = aws_lambda.get_account_settings()
        attachment = MessageAttachmentsClass()
        attachment.title = response['AccountUsage']['FunctionCount']
        message.attach(attachment)

        message.message_text = "The Function Count is:"
        return message.to_json()

    def log_stream(self, args, function_name):
        """To get the log Stream name  of the function, value is used in other
           function to get logs"""
        region = args['Region']
        aws_logs = boto3.client(service_name='logs', region_name=region,
                                api_version=None, use_ssl=True, verify=None,
                                endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                aws_secret_access_key=self.aws_secret_token,
                                aws_session_token=None, config=None)

        # To get the logstreamName if exists or return 0
        try:
            log_group_name = "/aws/lambda/"+function_name
            response = aws_logs.describe_log_streams(
                logGroupName=log_group_name, limit=1)
            return response['logStreams'][0]['logStreamName']

        except:
            return 0


    def get_logs(self, args):
        """To get the logs of the function"""
        region = args['Region']
        function_name = args['FunctionName']
        message = MessageClass()
        attachment = MessageAttachmentsClass()
        logstream = self.log_stream(args, function_name)

        # If Logstream is 0 then the Logs dosen't exist
        if logstream ==0:
            message.message_text = "There are no logs for that Function or the Log" \
                                   " group name and the Function Name are mismatched"
            return message.to_json()

        aws_lambda = boto3.client(service_name='logs', region_name=region,
                                  api_version=None, use_ssl=True, verify=None,
                                  endpoint_url=None, aws_access_key_id=self.aws_access_key,
                                  aws_secret_access_key=self.aws_secret_token,
                                  aws_session_token=None, config=None)
        log_group_name = "/aws/lambda/"+function_name

        # The following while loop is to find the i till which last log exists, for usage in get_log_events
        i = 0
        strin=""
        while strin != "START":
            response = aws_lambda.get_log_events(
                logGroupName=log_group_name,
                logStreamName=logstream,
                limit=i+1
            )
            string=str(response['events'][0]['message'])
            i = i+1
            strin = string[:5]

        #
        response = aws_lambda.get_log_events(
            logGroupName=log_group_name,
            logStreamName=logstream,
            limit=i
        )
        events = [event['message'] for event in response['events']]
        for event in events:
            attachment.text = event
            message.attach(attachment)

        message.message_text = "The Event logs are:"
        return message.to_json()

    def region(self, args):
        """ Basic inactive function to get dynamic inputs in  all other functions."""
        m = MessageClass()
        data = {'list': []}
        data['list'].append({"Region_Name": "us-east-1"})
        data['list'].append({"Region_Name": "us-east-2"})
        data['list'].append({"Region_Name": "us-west-1"})
        data['list'].append({"Region_Name": "us-west-2"})
        data['list'].append({"Region_Name": "ap-northeast-1"})
        data['list'].append({"Region_Name": "ap-northeast-2"})
        data['list'].append({"Region_Name": "ap-south-1"})
        data['list'].append({"Region_Name": "ap-southeast-1"})
        data['list'].append({"Region_Name": "ap-southeast-1"})
        data['list'].append({"Region_Name": "ca-central-1"})
        data['list'].append({"Region_Name": "eu-central-1"})
        data['list'].append({"Region_Name": "eu-west-1"})
        data['list'].append({"Region_Name": "eu-west-2"})
        data['list'].append({"Region_Name": "eu-west-3"})
        data['list'].append({"Region_Name": "sa-east-1"})
        m.data = data
        return m.to_json()
