import { useBilling } from "../context/BillingContext";

export function useSoftBlock() {
  const { block } = useBilling();
  return block.soft_block;
}
