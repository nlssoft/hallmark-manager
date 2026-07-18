import type {  ProfileResponse } from "../types/backendTypes/apiAuth";
import type { Profile} from "../types/frontedTypes/auth";


export function mapProfile(data: ProfileResponse | null | undefined): Profile | null{
    if (!data){
        return null;
    }
    return {
        number: data.number,
        companyName: data.company_name,
        companyAddress: data.company_address,
        officeNumber1: data.office_number1,
        officeNumber2: data.office_number2,
    }
}