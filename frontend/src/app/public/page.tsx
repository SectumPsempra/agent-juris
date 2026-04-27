import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ padding: "2rem" }}>
      <p>Landing page placeholder.</p>
      <ul>
        <li>
          <Link href="/pricing">Pricing</Link>
        </li>
        <li>
          <Link href="/login">Login</Link>
        </li>
        <li>
          <Link href="/dashboard">Dashboard</Link>
        </li>
      </ul>
    </main>
  );
}
