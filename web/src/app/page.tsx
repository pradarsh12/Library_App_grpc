import Link from "next/link";

const sections = [
  {
    href: "/books",
    title: "Books",
    description: "Browse the catalog, add new titles, and manage copies.",
  },
  {
    href: "/members",
    title: "Members",
    description: "Register members and keep their details up to date.",
  },
  {
    href: "/loans",
    title: "Loans",
    description: "Borrow and return books, and see who has what checked out.",
  },
];

export default function HomePage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Welcome</h1>
      <p className="mt-1 text-sm text-slate-500">
        Neighborhood Library
      </p>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {sections.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="rounded-lg border border-slate-200 bg-white p-5 transition-colors hover:border-slate-400"
          >
            <h2 className="font-medium text-slate-900">{s.title}</h2>
            <p className="mt-1 text-sm text-slate-500">{s.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
