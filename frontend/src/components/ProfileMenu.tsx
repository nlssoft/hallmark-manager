import type { option, ProfileMenuProps } from "../types/frontedTypes/navbar";
import { LogOut } from "lucide-react";

export function ProfileMenu({ options, user, fn, logoutFn }: ProfileMenuProps) {
    if (!user.isParent) {
        options = options.filter((o) => !o.parentOnly);
    }

    return (
        <div className="absolute top-16 right-1 grid w-60 rounded-xl border border-gray-200 bg-white shadow-xl">
            <div className="mt-2 flex flex-col items-center rounded-md border border-transparent bg-gray-50 p-2">
                <h1 className="font-semibold text-gray-900">{user.username}</h1>
                <p className="font-sm leading-relaxed text-gray-500">
                    {user.email}
                </p>
            </div>

            <div className="grid items-center">
                {options.map((o: option) => {
                    const Icon = o.icon;

                    return (
                        <button
                            key={o.key}
                            onClick={() => fn(o.route)}
                            className="flex w-full cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                        >
                            <Icon className="text-gray-500" />
                            {o.name}
                        </button>
                    );
                })}
            </div>

            <button
                onClick={() => logoutFn()}
                className="flex w-full cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            >
                <LogOut className="text-red-400" />
                Logout
            </button>
        </div>
    );
}
