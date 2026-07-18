import type { User } from "./auth";
import type { LucideIcon } from "lucide-react";

export interface option{
    key: string;
    name: string;
    route: string;
    parentOnly: boolean;
    icon: LucideIcon;
}

export interface ProfileMenuProps{
    options: option[];
    user: User;
    fn: (route:string) => void;
    logoutFn: ()=> Promise<void>;

}