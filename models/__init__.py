# Import all models explicitly to avoid circular imports
from models.models import *
from models.auto_loan import *
from models.home_loan import *
from models.machine_loan import *
from models.personal_loan import *
from models.business_loan import *
from models.loan_against_property import *
from models.private_funding import *
from models.banner import *
from models.device import *
from models.service_registration import *
from models.service_request import *  # Import before payment_gateway
from models.service_job_log import *
from models.payment_gateway import *
from models.push_tokens import *
from models.setting import *