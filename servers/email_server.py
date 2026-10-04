import os

from dotenv import load_dotenv
import resend
from mcp.server.fastmcp import FastMCP

load_dotenv()


# --------------------------------------------------
# MCP server
# --------------------------------------------------

mcp = FastMCP("EmailServer")


# --------------------------------------------------
# Resend configuration
# --------------------------------------------------

resend.api_key = os.getenv("RESEND_API_KEY")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# --------------------------------------------------
# Email tool
# --------------------------------------------------

@mcp.tool()
def send_email(

    to: str,
    subject : str,
    body : str
    ) -> str:
    """
    Send an email to the specified recipient.
    """

    print(f"Sending email to : '{to}'")

    try:
        response = resend.Emails.send(
            {
                "from":SENDER_EMAIL,
                "to" : [to],
                "subject" : subject,
                "text" : body
            }
        )

        return (
            f"Email successfully sent to {to}."
            f"Email id : {response.get("id", "unknown")}"
        )
    except Exception as e:
        return f"Failed to send email :{str(e)}"

# --------------------------------------------------
# Start MCP server
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport='stdio')