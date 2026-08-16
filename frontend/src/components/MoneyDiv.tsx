import { Minus } from "lucide-react";
import { formatMoney } from "../utils/formaters";

function MoneyDiv({ amount, color }: { amount: number; color: string }) {
    if (amount > 0) {
        return (
            <div className={`w-full text-right ${color}`}>
                ₹{formatMoney(amount)}
            </div>
        );
    }

    return (
        <div className="flex w-full justify-end">
            <Minus className="text-gray-300" />
        </div>
    );
}

export default MoneyDiv;
