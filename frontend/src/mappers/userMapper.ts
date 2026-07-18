import type { UserResponse } from "../types/backendTypes/apiAuth";
import type { User } from "../types/frontedTypes/auth";
import { mapProfile } from "./profileMapper";

export function mapUser(data: UserResponse): User{
    return {
        publicId: data.public_id,
        username: data.username,
        email: data.email,
        isParent: data.is_parent,
        profile: mapProfile(data.profile)
    }
}
