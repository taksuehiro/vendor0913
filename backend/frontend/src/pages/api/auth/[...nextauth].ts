import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export default NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: { email: {}, password: {} },
      authorize: async (cred) => {
        if (cred?.email && cred?.password) {
          return { id: '1', email: cred.email };
        }
        return null;
      },
    })
  ],
  session: { strategy: "jwt" },
});
