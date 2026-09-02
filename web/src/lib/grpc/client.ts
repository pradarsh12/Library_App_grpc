import "server-only";

import path from "node:path";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";

// This file talks to the Python gRPC server (../../../src/server) directly
// over @grpc/grpc-js, using the *same* .proto sources it's built from
// (../../../proto) — no separate JS codegen step, no grpc-web/Envoy proxy.
// It must only ever run on the server: @grpc/grpc-js depends on Node's
// net/tls modules, so `server-only` throws if this ever gets imported from
// a Client Component bundle.

const PROTO_ROOT = path.resolve(process.cwd(), "..", "proto");
const WELL_KNOWN_ROOT = path.resolve(
  process.cwd(),
  "node_modules",
  "google-proto-files"
);

const packageDefinition = protoLoader.loadSync(
  [
    "library/v1/common.proto",
    "library/v1/book.proto",
    "library/v1/member.proto",
    "library/v1/loan.proto",
  ],
  {
    keepCase: false,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
    includeDirs: [PROTO_ROOT, WELL_KNOWN_ROOT],
  }
);

const proto = grpc.loadPackageDefinition(packageDefinition) as unknown as {
  library: {
    v1: {
      BookService: grpc.ServiceClientConstructor;
      MemberService: grpc.ServiceClientConstructor;
      LoanService: grpc.ServiceClientConstructor;
    };
  };
};

const SERVER_ADDR = process.env.GRPC_SERVER_ADDR ?? "localhost:50051";
const credentials = grpc.credentials.createInsecure();

export const bookClient = new proto.library.v1.BookService(
  SERVER_ADDR,
  credentials
);
export const memberClient = new proto.library.v1.MemberService(
  SERVER_ADDR,
  credentials
);
export const loanClient = new proto.library.v1.LoanService(
  SERVER_ADDR,
  credentials
);

/** Thrown for any failed RPC; carries the gRPC status code and message. */
export class GrpcCallError extends Error {
  constructor(
    public readonly code: grpc.status,
    message: string
  ) {
    super(message);
    this.name = "GrpcCallError";
  }
}

type UnaryMethod<TRequest, TResponse> = (
  request: TRequest,
  options: grpc.CallOptions,
  callback: (error: grpc.ServiceError | null, response: TResponse) => void
) => grpc.ClientUnaryCall;

const DEFAULT_TIMEOUT_MS = 8_000;

/**
 * Promisifies a unary grpc-js call. The dynamically-loaded clients above
 * have no static method types (they're built at runtime from the .proto
 * files), so callers name the RPC and supply the request/response types
 * explicitly, e.g. `call<GetBookRequest, Book>(bookClient, "GetBook", req)`.
 *
 * Always passes a deadline: if the backend is down, TCP refuses the
 * connection near-instantly and this rejects fast on its own — but if it's
 * merely unreachable (hung, firewalled, DB stuck) a call with no deadline
 * can hang indefinitely and leave the page loading forever. The deadline
 * turns that into a clean DEADLINE_EXCEEDED within a bounded time.
 */
export function call<TRequest, TResponse>(
  client: grpc.Client,
  methodName: string,
  request: TRequest,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<TResponse> {
  const untyped = client as unknown as Record<
    string,
    UnaryMethod<TRequest, TResponse>
  >;
  const options: grpc.CallOptions = { deadline: Date.now() + timeoutMs };
  return new Promise((resolve, reject) => {
    // Call via `untyped[methodName](...)`, not a variable holding the
    // function, so `this` inside grpc-js's implementation stays bound to
    // `client` (it needs `this.channel` etc.).
    untyped[methodName](request, options, (error, response) => {
      if (error) {
        reject(new GrpcCallError(error.code, error.details || error.message));
      } else {
        resolve(response);
      }
    });
  });
}
