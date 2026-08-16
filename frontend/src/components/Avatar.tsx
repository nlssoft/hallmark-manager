function Avatar({ logo }: { logo: string }) {
    return (
        <div className="flex h-8 w-9 items-center justify-center rounded-2xl bg-blue-100 text-blue-700">
            {logo}
        </div>
    );
}

export default Avatar;
