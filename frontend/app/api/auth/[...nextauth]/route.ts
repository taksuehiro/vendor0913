import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // ダミー認証
        if (credentials?.email === "test@example.com" && 
            credentials?.password === "password") {
          return {
            id: "1",
            email: "test@example.com",
            name: "テストユーザー"
          };
        }
        return null;
      }
    })
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async redirect({ url, baseUrl }) {
      // エラーページからのリダイレクトを防ぐ
      if (url.includes('/api/auth/error')) {
        return `${baseUrl}/login`;
      }
      return `${baseUrl}/dashboard`;
    }
  },
  session: {
    strategy: "jwt",
  },
});

export { handler as GET, handler as POST };


