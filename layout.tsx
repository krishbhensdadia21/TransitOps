import Link from "next/link";
import { ReactNode } from "react";

const navItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
  },
  {
    name: "Vehicles",
    href: "/dashboard/vehicles",
  },
  {
    name: "Drivers",
    href: "/dashboard/drivers",
  },
  {
    name: "Trips",
    href: "/dashboard/trips",
  },
  {
    name: "Fuel",
    href: "/dashboard/fuel",
  },
  {
    name: "Maintenance",
    href: "/dashboard/maintenance",
  },
  {
    name: "Expenses",
    href: "/dashboard/expenses",
  },
];

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen flex bg-gray-100">

      <aside className="w-72 bg-slate-900 text-white shadow-lg">

        <div className="p-6 border-b border-slate-700">

          <h1 className="text-2xl font-bold">
            TransitOps
          </h1>

          <p className="text-sm text-slate-300 mt-1">
            Smart Fleet Management
          </p>

        </div>

        <nav className="mt-6">

          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="block px-6 py-4 hover:bg-slate-800 transition-colors"
            >
              {item.name}
            </Link>
          ))}

        </nav>

        <div className="absolute bottom-0 w-72 border-t border-slate-700 p-6">

          <Link
            href="/login"
            className="block text-center bg-red-600 hover:bg-red-700 rounded-lg py-3 font-semibold"
          >
            Logout
          </Link>

        </div>

      </aside>

      <main className="flex-1 overflow-auto">
        {children}
      </main>

    </div>
  );
}