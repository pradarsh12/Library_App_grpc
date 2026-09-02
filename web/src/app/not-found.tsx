import { LinkButton } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-md py-16 text-center">
      <h1 className="text-lg font-semibold text-slate-900">Not found</h1>
      <p className="mt-2 text-sm text-slate-500">
        We couldn&apos;t find what you were looking for.
      </p>
      <LinkButton href="/" className="mt-4">
        Back home
      </LinkButton>
    </div>
  );
}
