import requests

def validate_mobile_number_api_call():
    # Define the URL of the SOAP service
    url = "https://leadservices.brobotinsurance.com/rgiChatbot/ChatbotIntegrationWrapper.asmx"

    # Craft the XML request body with the passed mobile number
    soap_body = f'''
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:CreateSRForChatbotWrap>
         <!--Optional:-->
         <tem:XML><![CDATA[
            <EndorsementRequests>
                <EndorsementRequest>
                    <CallerUserID>WhatsApp</CallerUserID>
                    <Password>WhatsApp@123</Password>
                    <CallerAppId>293</CallerAppId>
                    <UniqueRefNo>92707</UniqueRefNo>
                    <LOB>2</LOB>
                    <PolicyNo>160221923730000221</PolicyNo>
                    <ProductCode>2311</ProductCode>
                    <SrvcCallType>8</SrvcCallType>
                    <SrvcCallSubType>4</SrvcCallSubType>
                    <SrvcReqType>1166</SrvcReqType>
                    <CallerName>RIVA</CallerName>
                    <IsDocumentPendingCase>Y</IsDocumentPendingCase>
                    <CallerType>5</CallerType>
                    <Gender></Gender>
                    <Date_Of_Birth></Date_Of_Birth>
                    <Address1></Address1>
                    <Address2></Address2>
                    <City></City>
                    <District></District>
                    <State></State>
                    <Pincode></Pincode>
                    <TelephoneNo></TelephoneNo>
                    <CallReceivedFromNo>8697745125</CallReceivedFromNo>
                    <InsuredNo></InsuredNo>
                    <EmailId>kore@gmail.com</EmailId>
                    <CustomerRemark>Kore Catbot Test</CustomerRemark>
                        <AdditionalFields>
                            <ClaimFields>
                                <ClaimNo></ClaimNo>
                                <ClaimStatus></ClaimStatus>
                                <DateApproval></DateApproval>
                                <DocSubmissionDate></DocSubmissionDate>
                                <LastUpdateCLStatus></LastUpdateCLStatus>
                                <PaymentMode></PaymentMode>
                            </ClaimFields>
                            <SalesFields>
                                <AgentName></AgentName>
                                <AgentContactNo></AgentContactNo>
                                <InspectionID></InspectionID>
                            </SalesFields>
                        <EndorsementFields>
                            <CorrectCubicCapacity></CorrectCubicCapacity>
                            <CorrectDOB></CorrectDOB>
                            <CorrectIDV></CorrectIDV>
                            <CorrectManufactYr></CorrectManufactYr>
                            <CorrectRTO></CorrectRTO>
                            <Countries></Countries>
                            <Guardian></Guardian>
                            <NomineeAddress></NomineeAddress>
                            <NomineeDOB></NomineeDOB>
                            <PassportNumber></PassportNumber>
                            <PolicyStartDt></PolicyStartDt>
                            <RelatnwithProposer></RelatnwithProposer>
                            <VehicleRegNo></VehicleRegNo>
                            <VisaType></VisaType>
                            <NomineeName></NomineeName>
                            <AddressL1></AddressL1>
                            <AddressL2></AddressL2>
                            <AddressLine3></AddressLine3>
                            <AddressLine4></AddressLine4>
                            <State></State>
                            <District></District>
                            <City></City>
                            <Pincode></Pincode>
                            <FinanciarType>1</FinanciarType>
                            <FinancierName></FinancierName>
                            <FinancierAddress></FinancierAddress>
                            <ContactNumber></ContactNumber>
                            <EmailID1></EmailID1>
                            <Gender></Gender>
                            <AppointeeName></AppointeeName>
                            <RelationShipwithIns></RelationShipwithIns>
                            <Age></Age>
                            <DateofBirth></DateofBirth>
                            <CorrectMake></CorrectMake>
                            <CorrectModel></CorrectModel>
                        </EndorsementFields>
                        <PolicyFields>
                            <AgentBrokeContactDtl></AgentBrokeContactDtl>
                            <AgentBrokerName></AgentBrokerName>
                            <BankName></BankName>
                            <DateofTransaction></DateofTransaction>
                            <EmailId></EmailId>
                            <ModeofPayment></ModeofPayment>
                            <OrderTransactionNo></OrderTransactionNo>
                            <PolicyHolderName></PolicyHolderName>
                            <PolicyNo></PolicyNo>
                            <PremiumAmount></PremiumAmount>
                            <QuotationNo></QuotationNo>
                            </PolicyFields>
                        </AdditionalFields>
                </EndorsementRequest>
            </EndorsementRequests>
        ]]></tem:XML>
      </tem:CreateSRForChatbotWrap>
   </soapenv:Body>
</soapenv:Envelope>'''

    # Set the necessary headers
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/CreateSRForChatbotWrap"
    }

    # Make the POST request
    response = requests.post(url, data=soap_body, headers=headers)
    # Parse the response text
    raw_xml = response.text

    print(raw_xml)



import requests

# SOAP endpoint
url = "https://leadservices.brobotinsurance.com/rgiChatbot/ChatbotIntegrationWrapper.asmx"

# SOAP headers
headers = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": "http://tempuri.org/CreateSRForChatbotWrap"
}

# Replace with actual values
policy_number = 160221923730000221
phone_number = 8697745125
product_code = 2311
caller_name = "Riva"
# SOAP body
body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:CreateSRForChatbotWrap>
         <tem:XML><![CDATA[
            <EndorsementRequests>
                <EndorsementRequest>
                    <CallerUserID>WhatsApp</CallerUserID>
                    <Password>WhatsApp@123</Password>
                    <CallerAppId>293</CallerAppId>
                    <UniqueRefNo>92707</UniqueRefNo>
                    <LOB>2</LOB>
                    <PolicyNo>{policy_number}</PolicyNo>
                    <ProductCode>{product_code}</ProductCode>
                    <SrvcCallType>7</SrvcCallType>
                    <SrvcCallSubType>4</SrvcCallSubType>
                    <SrvcReqType>1281</SrvcReqType>
                    <CallerName>{caller_name}</CallerName>
                    <IsDocumentPendingCase>Y</IsDocumentPendingCase>
                    <CallerType>5</CallerType>
                    <Gender></Gender>
                    <Date_Of_Birth></Date_Of_Birth>
                    <Address1></Address1>
                    <Address2></Address2>
                    <City></City>
                    <District></District>
                    <State></State>
                    <Pincode></Pincode>
                    <TelephoneNo></TelephoneNo>
                    <CallReceivedFromNo>{phone_number}</CallReceivedFromNo>
                    <InsuredNo></InsuredNo>
                    <EmailId>kore@gmail.com</EmailId>
                    <CustomerRemark>Kore Catbot Test</CustomerRemark>
                    <AdditionalFields>
                        <ClaimFields/>
                        <SalesFields/>
                        <EndorsementFields/>
                        <PolicyFields/>
                    </AdditionalFields>
                </EndorsementRequest>
            </EndorsementRequests>
         ]]></tem:XML>
      </tem:CreateSRForChatbotWrap>
   </soapenv:Body>
</soapenv:Envelope>"""

# Send request
response = requests.post(url, data=body, headers=headers)

# Print response
print("Status Code:", response.status_code)
print("Response Text:", response.text)
